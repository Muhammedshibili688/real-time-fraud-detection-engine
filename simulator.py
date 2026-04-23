import redis
import json
import random
import uuid
import time
from datetime import datetime, timedelta

# ----------------------------------------------------------------
# CONNECTING REDIS
# ----------------------------------------------------------------
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# ----------------------------------------------------------------
# 1. GLOBAL CONFIGURATION
# ----------------------------------------------------------------
COUNTRY_PROFILES = {
    "US": {"currency": "USD", "ex_rate": 1.0,     "ppp": 1.0,    "tz": -5,  "lat_range": (24, 49),   "lon_range": (-125, -66),  "ip_prefix": "192.161"},
    "IN": {"currency": "INR", "ex_rate": 93.0,    "ppp": 26.8,   "tz": 5.5, "lat_range": (8, 37),    "lon_range": (68, 97),     "ip_prefix": "103.21"},
    "GB": {"currency": "GBP", "ex_rate": 0.84,    "ppp": 0.72,   "tz": 0,   "lat_range": (50, 60),   "lon_range": (-10, 2),     "ip_prefix": "25.10"},
    "DE": {"currency": "EUR", "ex_rate": 1.02,    "ppp": 0.85,   "tz": 1,   "lat_range": (47, 55),   "lon_range": (5, 15),      "ip_prefix": "46.15"},
    "JP": {"currency": "JPY", "ex_rate": 164.5,   "ppp": 94.0,   "tz": 9,   "lat_range": (30, 45),   "lon_range": (128, 145),   "ip_prefix": "1.72"},
    "BR": {"currency": "BRL", "ex_rate": 6.15,    "ppp": 2.8,    "tz": -3,  "lat_range": (-33, 5),   "lon_range": (-73, -34),   "ip_prefix": "177.10"},
    "ZA": {"currency": "ZAR", "ex_rate": 22.1,    "ppp": 8.2,    "tz": 2,   "lat_range": (-35, -22), "lon_range": (16, 33),     "ip_prefix": "41.13"},
    "SG": {"currency": "SGD", "ex_rate": 1.42,    "ppp": 1.25,   "tz": 8,   "lat_range": (1, 2),     "lon_range": (103, 104),   "ip_prefix": "175.41"},
    "AU": {"currency": "AUD", "ex_rate": 1.65,    "ppp": 1.5,    "tz": 11,  "lat_range": (-44, -10), "lon_range": (113, 154),   "ip_prefix": "1.128"},
    "NG": {"currency": "NGN", "ex_rate": 1950.0,  "ppp": 480.0,  "tz": 1,   "lat_range": (4, 14),    "lon_range": (2, 14),      "ip_prefix": "102.64"},
    "CA": {"currency": "CAD", "ex_rate": 1.48,    "ppp": 1.25,   "tz": -5,  "lat_range": (43, 70),   "lon_range": (-141, -52),  "ip_prefix": "99.224"},
    "MX": {"currency": "MXN", "ex_rate": 22.4,    "ppp": 10.2,   "tz": -6,  "lat_range": (14, 33),   "lon_range": (-118, -86),  "ip_prefix": "187.174"},
    "CH": {"currency": "CHF", "ex_rate": 0.94,    "ppp": 1.15,   "tz": 1,   "lat_range": (45, 48),   "lon_range": (5, 10),      "ip_prefix": "85.0"},
    "AE": {"currency": "AED", "ex_rate": 3.67,    "ppp": 2.7,    "tz": 4,   "lat_range": (22, 26),   "lon_range": (51, 56),     "ip_prefix": "94.200"},
    "CN": {"currency": "CNY", "ex_rate": 7.45,    "ppp": 4.1,    "tz": 8,   "lat_range": (18, 53),   "lon_range": (73, 135),    "ip_prefix": "36.96"},
    "SA": {"currency": "SAR", "ex_rate": 3.75,    "ppp": 2.6,    "tz": 3,   "lat_range": (16, 32),   "lon_range": (36, 55),     "ip_prefix": "212.118"},
    "FR": {"currency": "EUR", "ex_rate": 1.02,    "ppp": 0.82,   "tz": 1,   "lat_range": (42, 51),   "lon_range": (-5, 8),      "ip_prefix": "90.0"},
    "KR": {"currency": "KRW", "ex_rate": 1420.0,  "ppp": 850.0,  "tz": 9,   "lat_range": (34, 38),   "lon_range": (126, 130),   "ip_prefix": "1.176"},
    "TR": {"currency": "TRY", "ex_rate": 45.0,    "ppp": 12.0,   "tz": 3,   "lat_range": (36, 42),   "lon_range": (26, 45),     "ip_prefix": "78.162"},
    "ID": {"currency": "IDR", "ex_rate": 16500.0, "ppp": 5200.0, "tz": 7,   "lat_range": (-11, 6),   "lon_range": (95, 141),    "ip_prefix": "36.66"},
}

MERCHANTS = {
    "standard": ["Amazon", "Walmart", "Local_Grocery", "Target", "Shell", "Starbucks"],
    "digital":  ["Netflix", "Steam", "Spotify", "AppStore", "OpenAI_Plus"],
    "luxury":   ["Apple_Store", "Rolex_Boutique", "First_Class_Travel", "HighEnd_Electronics"],
    "high_risk":["Crypto_Exchange_Alpha", "Gambling_Site_X", "Offshore_Transfer"],
}

# ----------------------------------------------------------------
# 2. USER (Internal simulation state — never emitted in JSON)
# ----------------------------------------------------------------
class User:
    def __init__(self, user_id):
        self.user_id           = user_id
        self.home_country      = random.choice(list(COUNTRY_PROFILES.keys()))
        self.profile           = COUNTRY_PROFILES[self.home_country]

        # Raw observable attributes (emitted)
        self.base_spend_usd    = random.uniform(15, 120) * self.profile["ppp"]
        self.known_devices     = [f"dev_{uuid.uuid4().hex[:8]}"]  # fixed: was 'devices' in v1
        self.card_type         = random.choice(["Visa_Debit", "Mastercard_Gold", "Amex_Platinum"])

        # Internal simulation state (NOT emitted — drives realistic behaviour only)
        self.tx_history_usd    = []
        self.is_fraud_target   = random.random() < 0.05
        self.fraud_state       = "CLEAN"   # CLEAN -> PROBING -> EXPLOITING -> BURNED
        self.fraud_session_start = None
        self.fraud_device      = None

        # Add state to user
        self.current_ip = f"{self.profile['ip_prefix']}.{random.randint(0,255)}.{random.randint(0,255)}"

        cp = self.profile

        self.current_lat = random.uniform(*cp["lat_range"])
        self.current_lon = random.uniform(*cp["lon_range"])

        self.last_travel_time = datetime.utcnow()

    def get_local_hour(self):
        """Returns simulated local hour to suppress night-time transactions."""
        local_dt = datetime.utcnow() + timedelta(hours=self.profile["tz"])
        return local_dt.hour

    def record_spend(self, usd_amt):
        self.tx_history_usd.append(usd_amt)
        if len(self.tx_history_usd) > 10:
            self.tx_history_usd.pop(0)

# ----------------------------------------------------------------
# 3. TRANSACTION ENGINE — emits only raw, physically observable fields
#
#    What a real payment gateway captures at the terminal:
#      tx_id, timestamp, user_id, amount, currency, country,
#      lat, lon, ip, device_id, merchant_name, merchant_category,
#      card_type, is_fraud (label, for training only), pattern (label)
#
#    What does NOT belong here (compute downstream in feature pipeline):
#      geo_speed, impossible_travel, amount_zscore, velocity_1h,
#      country_change_flag, device_mismatch, etc.
# ----------------------------------------------------------------
def generate_raw_tx(user):
    override_country    = None
    fraud_pattern_label = "legit"

    # ── A. FRAUD STATE MACHINE ──────────────────────────────────
    if user.is_fraud_target:
        if user.fraud_state == "CLEAN" and random.random() < 0.01:
            user.fraud_state         = "PROBING"
            user.fraud_session_start = datetime.utcnow()
            user.fraud_device        = f"atk_{uuid.uuid4().hex[:5]}"

        elif user.fraud_state == "PROBING":
            elapsed = (datetime.utcnow() - user.fraud_session_start).total_seconds()
            if elapsed > 5:
                user.fraud_state = "EXPLOITING"

        elif user.fraud_state == "EXPLOITING" and random.random() < 0.15:
            user.fraud_state = "BURNED"

    if user.fraud_state == "BURNED":
        # If 30 seconds have passed, reset the user so they can be a target again
        if (datetime.utcnow() - user.fraud_session_start).total_seconds() > 300:
            user.fraud_state = "CLEAN"
            user.fraud_device = None
        else:
            return None # Still cooling down

    # ── B. AMOUNT ───────────────────────────────────────────────
    if user.fraud_state == "PROBING":
        usd_amt             = random.uniform(0.50, 5.00)
        fraud_pattern_label = "card_test"

    elif user.fraud_state == "EXPLOITING":
        usd_amt             = random.uniform(2500, 10000)
        fraud_pattern_label = "takeover"
        if random.random() < 0.6:
            override_country = random.choice(list(COUNTRY_PROFILES.keys()))

    else:
        # Suppress most transactions during local sleeping hours (1am–6am)
        if 1 <= user.get_local_hour() <= 6 and random.random() < 0.9:
            return None
        avg     = (sum(user.tx_history_usd) / len(user.tx_history_usd)
                   if user.tx_history_usd else user.base_spend_usd)
        usd_amt = random.uniform(avg * 0.7, avg * 1.3)

    # ── C. GEO & NETWORK ────────────────────────────────────────

    # 1. FRAUD override (highest priority)
    if override_country:
        tx_country = override_country
        cp = COUNTRY_PROFILES[tx_country]

        lat = random.uniform(*cp["lat_range"])
        lon = random.uniform(*cp["lon_range"])

    # 2. REAL TRAVEL (second priority)
    if random.random() < 0.01 and (datetime.utcnow() - user.last_travel_time).total_seconds() > 3600:
        new_country = random.choice(list(COUNTRY_PROFILES.keys()))
        user.home_country = new_country
        user.profile = COUNTRY_PROFILES[new_country]
        user.last_travel_time = datetime.utcnow()

        cp = user.profile

        lat = random.uniform(*cp["lat_range"])
        lon = random.uniform(*cp["lon_range"])

        tx_country = new_country

        user.current_ip = f"{cp['ip_prefix']}.{random.randint(0,255)}.{random.randint(0,255)}"


    # 3. NORMAL MOVEMENT
    else:
        tx_country = user.home_country
        cp = user.profile

        lat = user.current_lat + random.uniform(-0.005, 0.005)
        lon = user.current_lon + random.uniform(-0.005, 0.005)

        # clamp (critical)
        lat = max(min(lat, cp["lat_range"][1]), cp["lat_range"][0])
        lon = max(min(lon, cp["lon_range"][1]), cp["lon_range"][0])

    # IP ALWAYS from tx_country profile (no ambiguity)
    # 90% same IP, 10% change
    
    if random.random() < 0.9:
        ip = user.current_ip
    else:
        ip = f"{cp['ip_prefix']}.{random.randint(0,255)}.{random.randint(0,255)}"
        user.current_ip = ip 

    # ── D. DEVICE & MERCHANT ────────────────────────────────────
    
    # Fraudster uses injected attack device; legit user picks from known devices
    # occasional new device
    if random.random() < 0.05:
        new_device = f"dev_{uuid.uuid4().hex[:8]}"
        user.known_devices.append(new_device)
    
    device = (user.fraud_device
              if user.fraud_state != "CLEAN"
              else random.choice(user.known_devices))   # fixed: was user.devices

    if user.fraud_state == "PROBING":      cat = "digital"
    elif user.fraud_state == "EXPLOITING": cat = "high_risk"
    elif usd_amt > 1000:                   cat = "luxury"
    else:                                  cat = "standard"

    merchant = random.choice(MERCHANTS[cat])

    # ── E. UPDATE INTERNAL HISTORY ──────────────────────────────
    user.record_spend(usd_amt)

    # Upating location after transaction
    user.current_lat = lat
    user.current_lon = lon

    # ── F. RAW RECORD — only physically observable fields ───────
    return {
        "tx_id":            str(uuid.uuid4()),
        "timestamp":        datetime.utcnow().isoformat(),
        "user_id":          user.user_id,
        "amount":           round(usd_amt * cp["ex_rate"], 2),  # local currency
        "amount_usd":       round(usd_amt, 2),                  # normalised for sink
        "currency":         cp["currency"],
        "country":          tx_country,
        "lat":              lat,
        "lon":              lon,
        "ip":               ip,
        "device_id":        device,
        "merchant_name":    merchant,
        "merchant_category":cat,
        "card_type":        user.card_type,
        # ── Training labels (strip these in production inference) ──
        "is_fraud":         1 if user.fraud_state != "CLEAN" else 0,
        "pattern":          fraud_pattern_label,
    }

# ----------------------------------------------------------------
# 4. WRITER
# ----------------------------------------------------------------
def write_to_sink(tx, file_path="transactions.jsonl"):
    with open(file_path, "a") as f:
        f.write(json.dumps(tx) + "\n")

# ----------------------------------------------------------------
# 5. STREAM (transaction.json -> Redis)
# ----------------------------------------------------------------
def stream_tx(tx):
    r.xadd("transactions", {"data": json.dumps(tx)})

# ----------------------------------------------------------------
# 6. RUNNER
# ----------------------------------------------------------------
users = [User(f"USR_{i:04d}") for i in range(2500)]
print("Producer started → transactions.jsonl")

try:
    while True:
        for user in random.sample(users, 200):
            # If a fraud session is active, make it fire transactions very fast (60% chance per tick)
            prob = 0.6 if user.fraud_state in ["PROBING", "EXPLOITING"] else 0.08

            if random.random() < prob:
                tx = generate_raw_tx(user)
                if tx:
                    write_to_sink(tx)
                    stream_tx(tx)

                    # Velocity burst: exploiters fire 1–3 extra transactions immediately
                    if user.fraud_state == "EXPLOITING":
                        for _ in range(random.randint(1, 3)):
                            burst_tx = generate_raw_tx(user)
                            if burst_tx:
                                write_to_sink(burst_tx)
                                stream_tx(burst_tx)

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nProducer stopped.")