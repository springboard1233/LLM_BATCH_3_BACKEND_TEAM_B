from fastapi import APIRouter
from src.utils.fraud_dashboard.database import collection

router = APIRouter(prefix="/insights")

@router.get("/transaction_amounts")
def amount_insights():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "avg_amount": {"$avg": "$transaction_amount"},
                "max_amount": {"$max": "$transaction_amount"},
                "min_amount": {"$min": "$transaction_amount"},
            }
        }
    ]
    data = list(collection.aggregate(pipeline))[0]
    return data
