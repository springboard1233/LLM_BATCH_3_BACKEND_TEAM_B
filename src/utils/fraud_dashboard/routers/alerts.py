from fastapi import APIRouter
from database import collection

router = APIRouter(prefix="/alerts")

@router.get("/suspicious")
def suspicious_transactions():
    pipeline = [
        {"$match": {"transaction_amount": {"$gt": 0.9}}},
        {"$sort": {"transaction_amount": -1}},
        {"$limit": 10}
    ]
    return list(collection.aggregate(pipeline))
