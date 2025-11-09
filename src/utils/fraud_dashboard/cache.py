# This is the complete, corrected code for:
# src/utils/utilities/cache.py

import sys
import os
import redis
from dotenv import load_dotenv

# --- NEW PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=dotenv_path)
# --- END OF NEW PATH FIX ---

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = None

def get_redis_client():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            redis_client.ping()
            print("Successfully connected to Redis.")
        except Exception as e:
            print(f"CRITICAL ERROR connecting to Redis: {e}")
            redis_client = None
    return redis_client

def set_in_cache(client: redis.Redis, key: str, value: str, ttl_seconds: int = 3600):
    if client:
        try:
            client.setex(key, ttl_seconds, value)
        except Exception as e:
            print(f"Error setting cache for key '{key}': {e}")

def get_from_cache(client: redis.Redis, key: str) -> str | None:
    if client:
        try:
            return client.get(key)
        except Exception as e:
            print(f"Error getting cache for key '{key}': {e}")
    return None