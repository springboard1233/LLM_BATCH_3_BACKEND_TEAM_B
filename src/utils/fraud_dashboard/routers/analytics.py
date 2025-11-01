from fastapi import APIRouter
from src.utils.fraud_dashboard.database import collection

router = APIRouter(prefix="/analytics")

@router.get("/fraud_trend")
def fraud_trend():
    pipeline = [
        {
            "$group": {
                "_id": { 
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"}
                },
                "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}},
                "total": {"$sum": 1}
            }
        }
    ]
    return list(collection.aggregate(pipeline))



@router.get("/fraud_by_channel")
def fraud_by_channel():
    pipeline = [
        {
            "$group": {
                "_id": "$channel_mobile",
                "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}},
                "total": {"$sum": 1}
            }
        }
    ]
    return list(collection.aggregate(pipeline))
