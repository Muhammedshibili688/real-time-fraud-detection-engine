import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv() # This loads the variables from your .env file

# Project root directory (for constructing paths)
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
PROJECT_ROOT = Path(os.getcwd())
print(f"Project Root: {PROJECT_ROOT}")

MIN_RECORDS_FOR_TRAINING = 200000  # 2 Lakhs
MAX_RECORDS_TO_KEEP = 400000      # 4 Lakhs

# AWS S3 bucket name
# Now, if the variable exists in the OS, use it. 
# Otherwise, use the "default" (the second value).
TRAINING_BUCKET_NAME = os.getenv("TRAINING_BUCKET_NAME", "fraud-detection-engine-bucket")

# Redis constants
STREAM_NAME = os.getenv("STREAM_NAME", "transactions")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# For Producer
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