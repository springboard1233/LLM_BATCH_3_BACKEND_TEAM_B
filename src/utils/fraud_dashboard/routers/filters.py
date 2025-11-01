from fastapi import APIRouter
from src.utils.fraud_dashboard.database import collection
from datetime import datetime

router = APIRouter(prefix="/filter")

@router.get("/transactions")
def filter_transactions(
    start_date: str = None,
    end_date: str = None,
    channel: str = None
):
    query = {}

    if start_date and end_date:
        query["timestamp"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }

    if channel:
        query[channel] = 1

    data = list(collection.find(query, {"_id": 0}))
    return data
