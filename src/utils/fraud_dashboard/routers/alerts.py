from fastapi import APIRouter
from database import collection
from utils import convert_objectid

router = APIRouter(prefix="/alerts")

@router.get("/suspicious")
def suspicious_transactions():
    pipeline = [
        {"$match": {"transaction_amount": {"$gt": 0.9}}},
        {"$sort": {"transaction_amount": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return convert_objectid(result)
