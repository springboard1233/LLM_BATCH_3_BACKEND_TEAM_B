from fastapi import APIRouter
from src.utils.fraud_dashboard.database import collection

router = APIRouter(prefix="/analytics")

@router.get("/fraud-trend")
def fraud_trend():
    """Get fraud trends over time"""
    pipeline = [
        {
            "$group": {
                "_id": { 
                    "day": "$day",
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"}
                },
                "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}},
                "total": {"$sum": 1},
                "fraud_amount": {"$sum": {"$cond": ["$is_fraud", "$transaction_amount", 0]}}
            }
        },
        {"$sort": {"_id.day": 1}}
    ]
    return list(collection.aggregate(pipeline))

@router.get("/fraud-by-channel")
def fraud_by_channel():
    """Get fraud distribution by channel"""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "mobile_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_mobile", 1]}]}, 1, 0]}},
                "atm_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_atm", 1]}]}, 1, 0]}},
                "pos_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_pos", 1]}]}, 1, 0]}},
                "web_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_web", 1]}]}, 1, 0]}},
                "mobile_total": {"$sum": "$channel_mobile"},
                "atm_total": {"$sum": "$channel_atm"},
                "pos_total": {"$sum": "$channel_pos"},
                "web_total": {"$sum": "$channel_web"}
            }
        }
    ]
    return list(collection.aggregate(pipeline))

@router.get("/fraud-loss")
def fraud_loss():
    """Get total fraud loss amount"""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_fraud_loss": {"$sum": {"$cond": ["$is_fraud", "$transaction_amount", 0]}},
                "avg_fraud_amount": {"$avg": {"$cond": ["$is_fraud", "$transaction_amount", None]}},
                "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}}
            }
        }
    ]
    return list(collection.aggregate(pipeline))