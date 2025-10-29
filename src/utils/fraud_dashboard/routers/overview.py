from fastapi import APIRouter
from database import collection
from cache import cache
from utils.helpers import get_db_last_update
from datetime import datetime

router = APIRouter(prefix="/overview")

@router.get("/stats")
def overview_stats():

    db_time = get_db_last_update()

    # If cached and DB hasn't changed → return cache
    if cache["overview"] and cache["cached_at"] == db_time:
        return cache["overview"]

    # Otherwise compute fresh data
    total = collection.count_documents({})
    fraud = collection.count_documents({"is_fraud": 1})
    legit = total - fraud

    result = {
        "total_records": total,
        "fraud_cases": fraud,
        "non_fraud_cases": legit,
        "fraud_percentage": round((fraud/total)*100, 2),
        "non_fraud_percentage": round((legit/total)*100, 2)
    }

    # Store in cache
    cache["overview"] = result
    cache["cached_at"] = db_time

    return result
