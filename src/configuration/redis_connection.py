import redis
import os

class RedisClient:
    def __init__(self, host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT")):
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                decode_response = True
                )
            self.client.ping()
            print("Connected to Redis successfully!")

        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            self.client = None
        
        except Exception as e:
            print(f"An Unexpectederror occurred while connecting to Redis: {e}")
            self.client = None