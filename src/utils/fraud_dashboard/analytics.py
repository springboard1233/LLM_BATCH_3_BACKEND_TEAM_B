from fastapi import APIRouter
from database import collection
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard_analytics():

    # 1️⃣ Transaction Volume by `day`
    volume_data = list(collection.aggregate([
        {
            "$group": {
                "_id": "$day",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]))

    # 2️⃣ Channel Distribution
    channel_distribution = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "atm": {"$sum": "$channel_atm"},
                "mobile": {"$sum": "$channel_mobile"},
                "pos": {"$sum": "$channel_pos"},
                "web": {"$sum": "$channel_web"},
            }
        }
    ]))

    # 3️⃣ Fraud loss vs legit volume
    fraud_legit = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "fraud_loss": {
                    "$sum": {
                        "$cond": [{"$eq": ["$is_fraud", 1]}, "$transaction_amount", 0]
                    }
                },
                "legit_volume": {
                    "$sum": {
                        "$cond": [{"$eq": ["$is_fraud", 0]}, "$transaction_amount", 0]
                    }
                }
            }
        }
    ]))

    fraud_loss = fraud_legit[0]["fraud_loss"]
    legit_volume = fraud_legit[0]["legit_volume"]

    # 4️⃣ Hourly Distribution
    hourly_distribution = list(collection.aggregate([
        {
            "$group": {
                "_id": "$hour",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]))

    # 5️⃣ Daily Activity (Last 7 Days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    daily_activity = list(collection.aggregate([
    {
        "$group": {
            "_id": {"$dayOfMonth": "$timestamp"},
            "count": {"$sum": 1}
        }
    },
    {"$sort": {"_id": 1}}
]))


    return {
        "volume_data": volume_data,
        "channel_distribution": channel_distribution,
        "fraud_loss": fraud_loss,
        "legit_volume": legit_volume,
        "hourly_distribution": hourly_distribution,
        "daily_activity": daily_activity,
    }
