import os
import redis
from typing import Optional

class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                raise ValueError("REDIS_URL environment variable is not set")
            cls._instance = redis.Redis.from_url(redis_url)
        return cls._instance

# Create a global instance for easy access
redis_client = RedisClient.get_instance() 