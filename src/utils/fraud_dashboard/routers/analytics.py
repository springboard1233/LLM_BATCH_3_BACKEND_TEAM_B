import sys
import os
from fastapi import APIRouter

# --- NEW PATH FIX ---
# This code manually adds your project's root folder to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 4 levels: routers -> fraud_dashboard -> utils -> src -> ROOT
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- END OF NEW PATH FIX ---

# --- THIS IMPORT IS NOW CORRECT ---
# It imports the FUNCTION from the correct 'utilities' folder
from src.utils.fraud_dashboard.database import get_collection
# -----------------------------------

router = APIRouter(prefix="/analytics")

# --- THIS IS NOW CORRECT ---
# We CALL the function to get the 'transactions' collection
try:
    collection = get_collection("transactions")
except Exception as e:
    print(f"CRITICAL ERROR in analytics.py: Could not get 'transactions' collection. {e}")
    collection = None
# ---------------------------

@router.get("/fraud_trend", tags=["Analytics"])
def fraud_trend():
    """Get fraud trends over time"""
    if collection is None:
        return {"error": "Database connection failed"}
        
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

@router.get("/fraud_by_channel")
def fraud_by_channel():
    """Get fraud distribution by channel"""
    if collection is None:
        return {"error": "Database connection failed"}
        
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

@router.get("/fraud_loss")
def fraud_loss():
    """Get total fraud loss amount"""
    if collection is None:
        return {"error": "Database connection failed"}
        
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

@router.get("/dashboard")
def dashboard():
    """Return aggregated analytics data expected by the frontend dashboard"""
    if collection is None:
        return {"error": "Database connection failed"}

    total_stats = list(
        collection.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "total_transactions": {"$sum": 1},
                        "fraud_transactions": {
                            "$sum": {"$cond": ["$is_fraud", 1, 0]}
                        },
                        "fraud_loss": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$is_fraud", 1]},
                                    "$transaction_amount",
                                    0,
                                ]
                            }
                        },
                        "legit_volume": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$is_fraud", 0]},
                                    "$transaction_amount",
                                    0,
                                ]
                            }
                        },
                    }
                }
            ]
        )
    )

    if not total_stats:
        return {
            "analytics_metrics": {
                "totalTransactions": 0,
                "fraudRate": "0.00",
                "fraudLoss": 0,
                "legitimateVolume": 0,
            },
            "volume_by_day_data": [],
            "channel_data": [],
            "activity_data": {"hourly": [], "daily": []},
        }

    stats = total_stats[0]
    total_transactions = stats.get("total_transactions", 0)
    fraud_transactions = stats.get("fraud_transactions", 0)
    fraud_rate = (
        f"{(fraud_transactions / total_transactions * 100):.2f}"
        if total_transactions > 0
        else "0.00"
    )

    analytics_metrics = {
        "totalTransactions": total_transactions,
        "fraudRate": fraud_rate,
        "fraudLoss": stats.get("fraud_loss", 0),
        "legitimateVolume": stats.get("legit_volume", 0),
    }

    volume_data = list(
        collection.aggregate(
            [
                {
                    "$group": {
                        "_id": "$day",
                        "volume": {"$sum": "$transaction_amount"},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )
    )
    volume_by_day_data = [
        {"name": f"Day {item.get('_id')}", "volume": item.get("volume", 0)}
        for item in volume_data
        if item.get("_id") is not None
    ]

    channel_stats = list(
        collection.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "mobile": {"$sum": "$channel_mobile"},
                        "atm": {"$sum": "$channel_atm"},
                        "pos": {"$sum": "$channel_pos"},
                        "web": {"$sum": "$channel_web"},
                    }
                }
            ]
        )
    )
    channel_data = []
    if channel_stats:
        channels = channel_stats[0]
        channel_data = [
            {"name": "Mobile", "value": channels.get("mobile", 0), "color": "#3B82F6"},
            {"name": "ATM", "value": channels.get("atm", 0), "color": "#10B981"},
            {"name": "POS", "value": channels.get("pos", 0), "color": "#F59E0B"},
            {"name": "Web", "value": channels.get("web", 0), "color": "#EF4444"},
        ]

    hourly_data = list(
        collection.aggregate(
            [
                {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )
    )
    hourly = [
        {"name": f"{item.get('_id')}:00", "transactions": item.get("count", 0)}
        for item in hourly_data
        if item.get("_id") is not None
    ]

    daily_data = list(
        collection.aggregate(
            [
                {"$group": {"_id": "$weekday", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )
    )
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    daily = []
    for item in daily_data:
        idx = item.get("_id")
        if isinstance(idx, int) and 0 <= idx < len(day_names):
            daily.append(
                {"name": day_names[idx], "transactions": item.get("count", 0)}
            )

    return {
        "analytics_metrics": analytics_metrics,
        "volume_by_day_data": volume_by_day_data,
        "channel_data": channel_data,
        "activity_data": {"hourly": hourly, "daily": daily},
    }







