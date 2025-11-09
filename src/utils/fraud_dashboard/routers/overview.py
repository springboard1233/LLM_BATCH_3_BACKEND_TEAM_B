# # This is the complete, corrected code for:
# src/utils/fraud_dashboard/routers/overview.py

import sys
import os
from fastapi import APIRouter, Depends
import json
from redis.client import Redis

# --- NEW PATH FIX ---
# This code manually adds your project's root folder to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 4 levels: routers -> fraud_dashboard -> utils -> src -> ROOT
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- END OF NEW PATH FIX ---

# --- THESE IMPORTS ARE NOW CORRECT ---
from src.utils.fraud_dashboard.database import get_collection
from src.utils.fraud_dashboard.cache import get_redis_client, get_from_cache, set_in_cache
# from src.utils.utilities.helpers import get_db_last_update # This line is commented out as it's not used
# -----------------------------------

router = APIRouter(prefix="/overview")

# --- THIS IS NOW CORRECT ---
# We CALL the function to get the 'transactions' collection
try:
    collection = get_collection("transactions")
except Exception as e:
    print(f"CRITICAL ERROR in overview.py: Could not get 'transactions' collection. {e}")
    collection = None
# ---------------------------

@router.get("/stats")
def overview_stats(cache: Redis = Depends(get_redis_client)):
    
    cache_key = "overview_stats"
    
    # --- 1. NEW CACHE LOGIC ---
    # Try to get from Redis cache first
    cached_data = get_from_cache(cache, cache_key)
    if cached_data:
        print("--- DEBUG: Overview stats found in cache ---")
        return json.loads(cached_data)
    # --------------------------

    print("--- DEBUG: Overview stats not in cache, computing... ---")
    if collection is None:
        return {"error": "Database connection failed"}

    # --- 2. NEW DATABASE LOGIC ---
    # Compute fresh data
    total = collection.count_documents({})
    fraud = collection.count_documents({"is_fraud": 1})
    legit = total - fraud

    if total == 0: # Avoid division by zero
        return {"error": "No data in collection"}

    result = {
        "total_records": total,
        "fraud_cases": fraud,
        "non_fraud_cases": legit,
        "fraud_percentage": round((fraud/total)*100, 2),
        "non_fraud_percentage": round((legit/total)*100, 2)
    }
    # ---------------------------

    # --- 3. NEW CACHE LOGIC ---
    # Store in Redis cache for 1 hour (3600 seconds)
    set_in_cache(cache, cache_key, json.dumps(result), ttl_seconds=3600)
    # --------------------------

    return result