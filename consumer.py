import redis
import json
from datetime import datetime
import math
import atexit
import time

# ----------------------------------------------------------------
# REDIS CONNECTION
# ----------------------------------------------------------------
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
STREAM_NAME = "transactions"

# ----------------------------------------------------------------
# HAVERSINE DISTANCE
# ----------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# ----------------------------------------------------------------
# BUFFERED WRITER
# ----------------------------------------------------------------
buffer = []

def save_enriched(tx, path="features.jsonl"):
    buffer.append(tx)
    if len(buffer) >= 1000:
        flush_buffer(path)

def flush_buffer(path="features.jsonl"):
    """FIX Bug 4: called on exit so no records are lost."""
    if buffer:
        with open(path, "a") as f:
            for row in buffer:
                f.write(json.dumps(row) + "\n")
        buffer.clear()

atexit.register(flush_buffer)  # guarantees flush on Ctrl+C or normal exit

# ----------------------------------------------------------------
# MAIN CONSUMER
# ----------------------------------------------------------------
counter = 0

def consume():
    global counter
    last_id = "0-0"  # Start from the very beginning of the stream
    processed_count = 0
    MAX_RECORDS = 500_000

    while True:
        total_in_redis = r.xlen(STREAM_NAME)
        messages = r.xread({STREAM_NAME: last_id}, block=5000, count=100)
        if not messages:
            # Check current status
            if processed_count >= total_in_redis:

                print(f"All caught up! Processed: {processed_count}/{total_in_redis}")
            
            time.sleep(2) # Wait before trying again
            continue

        for stream, msgs in messages:
            for msg_id, fields in msgs:

                tx        = json.loads(fields["data"])

                last_id   = msg_id
                processed_count += 1

                user_id   = tx["user_id"]
                amount    = tx["amount_usd"]
                lat       = tx["lat"]
                lon       = tx["lon"]
                device    = tx["device_id"]
                ip        = tx["ip"]
                country   = tx["country"]
                timestamp = datetime.fromisoformat(tx["timestamp"])

                # ── USER STATE (read only — no mutation yet) ─────────
                state_key = f"user:{user_id}"
                state     = r.hgetall(state_key)

                last_lat  = float(state.get("last_lat", lat))
                last_lon  = float(state.get("last_lon", lon))
                last_time = state.get("last_time")

                avg_amount = float(state.get("avg_amount", amount))
                tx_count   = int(state.get("tx_count", 0))

                # FIX Bug 1 & 2: load lists WITHOUT adding current device/ip yet.
                # The check must happen against the STORED list, not after mutation.
                MAX_DEVICES = 10
                MAX_IPS     = 20

                known_devices = json.loads(state.get("devices", "[]"))
                known_ips     = json.loads(state.get("ips",     "[]"))

                last_country         = state.get("last_country", country)
                device_switch_count  = int(state.get("device_switch_count", 0))
                ip_switch_count      = int(state.get("ip_switch_count",     0))

                # ── COUNTRY STATE ────────────────────────────────────
                country_key   = f"country:{country}"
                c_state       = r.hgetall(country_key)
                country_total = float(c_state.get("total_amount", 0))
                country_count = int(c_state.get("tx_count", 0))
                country_avg   = country_total / country_count if country_count > 0 else amount

                # ── FEATURE ENGINEERING ──────────────────────────────

                # 1. Amount ratio vs user baseline
                amount_ratio = round(amount / avg_amount, 2) if avg_amount > 0 else 1.0

                # 2. Geo distance from last known position
                distance = haversine(last_lat, last_lon, lat, lon)

                # 3. Time delta
                if last_time:
                    dt_hours = max(
                        (timestamp - datetime.fromisoformat(last_time)).total_seconds() / 3600,
                        1e-3
                    )
                else:
                    dt_hours = 1.0

                # 4. Geo speed + impossible travel flag
                geo_speed        = min(distance / dt_hours, 2000)
                impossible_travel = 1 if geo_speed > 900 else 0

                # 5. FIX Bug 1: check BEFORE adding to list
                is_new_device = 1 if device not in known_devices else 0
                is_new_ip     = 1 if ip     not in known_ips     else 0

                # Increment switch counters based on the correct flags
                if is_new_device:
                    device_switch_count += 1
                if is_new_ip:
                    ip_switch_count += 1

                # 6. Country change
                country_change = 1 if country != last_country else 0

                # 7. User amount vs country average
                user_country_ratio = round(amount / country_avg, 2) if country_avg > 0 else 1.0

                # ── UPDATE STATE (after feature computation) ─────────
                # FIX Bug 2: single controlled add, capped to MAX_*
                if is_new_device:
                    known_devices.append(device)
                    if len(known_devices) > MAX_DEVICES:
                        known_devices = known_devices[-MAX_DEVICES:]

                if is_new_ip:
                    known_ips.append(ip)
                    if len(known_ips) > MAX_IPS:
                        known_ips = known_ips[-MAX_IPS:]

                new_avg = (avg_amount * tx_count + amount) / (tx_count + 1)

                r.hset(state_key, mapping={
                    "last_lat":            lat,
                    "last_lon":            lon,
                    "last_time":           tx["timestamp"],
                    "avg_amount":          new_avg,
                    "tx_count":            tx_count + 1,
                    "devices":             json.dumps(known_devices),
                    "ips":                 json.dumps(known_ips),
                    "last_country":        country,
                    "device_switch_count": device_switch_count,
                    "ip_switch_count":     ip_switch_count,
                })

                r.hset(country_key, mapping={
                    "total_amount": country_total + amount,
                    "tx_count":     country_count + 1,
                })

                # ── ENRICHED OUTPUT ──────────────────────────────────
                enriched = {
                    **tx,
                    "amount_ratio":        amount_ratio,
                    "geo_distance":        round(distance, 2),
                    "geo_speed":           round(geo_speed, 2),
                    "impossible_travel":   impossible_travel,
                    "is_new_device":       is_new_device,
                    "is_new_ip":           is_new_ip,
                    "device_switch_count": device_switch_count,
                    "ip_switch_count":     ip_switch_count,
                    "country_change":      country_change,
                    "country_avg_amount":  round(country_avg, 2),
                    "user_country_ratio":  user_country_ratio,
                }

                save_enriched(enriched)

                counter += 1
                if counter % 10_000 == 0:
                    print(f"  Processed {counter:,} records")

                if counter >= MAX_RECORDS:
                    print(f"Reached limit of {MAX_RECORDS:,} — stopping.")
                    flush_buffer()
                    return

# ----------------------------------------------------------------
# RUN
# ----------------------------------------------------------------
if __name__ == "__main__":
    try:
        r.ping()
        print("Consumer started → features.jsonl")
        consume()
    except KeyboardInterrupt:
        print("\nConsumer stopped — flushing buffer...")
        flush_buffer()
    except Exception as e:
        flush_buffer()
        raise e