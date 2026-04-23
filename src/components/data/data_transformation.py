import math
import json
from datetime import datetime
from src.constants import COUNTRY_PROFILES

class FraudFeatureEngineer:
    def __init__(self):
        self.R = 6371  # Earth radius for Haversine

    def haversine(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return self.R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def transform_data(self, tx, user_state):
        """
        Calculates all features based on RAW tx and Redis USER_STATE.
        """
        # 1. Basic Stats from Redis
        last_lat = float(user_state.get("last_lat", tx["lat"]))
        last_lon = float(user_state.get("last_lon", tx["lon"]))
        last_time = user_state.get("last_time")
        avg_amount = float(user_state.get("avg_amount", tx["amount_usd"]))
        tx_count = int(user_state.get("tx_count", 0))
        
        # 2. Geo Math
        distance = self.haversine(last_lat, last_lon, tx["lat"], tx["lon"])
        if last_time:
            dt_hours = max((datetime.fromisoformat(tx["timestamp"]) - 
                            datetime.fromisoformat(last_time)).total_seconds() / 3600, 1e-3)
        else:
            dt_hours = 1.0
        
        geo_speed = min(distance / dt_hours, 2000)

        # 3. Behavioral Features
        known_devices = json.loads(user_state.get("devices", "[]"))
        known_ips = json.loads(user_state.get("ips", "[]"))
        
        is_new_device = 1 if tx["device_id"] not in known_devices else 0
        is_new_ip = 1 if tx["ip"] not in known_ips else 0

        # 4. Final Object (The Enriched JSON)
        enriched = {
            **tx,
            "amount_ratio": round(tx["amount_usd"] / avg_amount, 2) if avg_amount > 0 else 1.0,
            "geo_distance": round(distance, 2),
            "geo_speed": round(geo_speed, 2),
            "impossible_travel": 1 if geo_speed > 900 else 0,
            "is_new_device": is_new_device,
            "is_new_ip": is_new_ip
        }
        return enriched
