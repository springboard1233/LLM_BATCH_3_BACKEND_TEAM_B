# from fastapi import APIRouter
# from database import collection
# from datetime import datetime, timedelta

# router = APIRouter(prefix="/analytics", tags=["Analytics"])


# @router.get("/dashboard")
# def dashboard_analytics():

#     # 1️⃣ Transaction Volume by `day`
#     volume_data = list(collection.aggregate([
#         {
#             "$group": {
#                 "_id": "$day",
#                 "count": {"$sum": 1}
#             }
#         },
#         {"$sort": {"_id": 1}}
#     ]))

#     # 2️⃣ Channel Distribution
#     channel_distribution = list(collection.aggregate([
#         {
#             "$group": {
#                 "_id": None,
#                 "atm": {"$sum": "$channel_atm"},
#                 "mobile": {"$sum": "$channel_mobile"},
#                 "pos": {"$sum": "$channel_pos"},
#                 "web": {"$sum": "$channel_web"},
#             }
#         }
#     ]))

#     # 3️⃣ Fraud loss vs legit volume
#     fraud_legit = list(collection.aggregate([
#         {
#             "$group": {
#                 "_id": None,
#                 "fraud_loss": {
#                     "$sum": {
#                         "$cond": [{"$eq": ["$is_fraud", 1]}, "$transaction_amount", 0]
#                     }
#                 },
#                 "legit_volume": {
#                     "$sum": {
#                         "$cond": [{"$eq": ["$is_fraud", 0]}, "$transaction_amount", 0]
#                     }
#                 }
#             }
#         }
#     ]))

#     fraud_loss = fraud_legit[0]["fraud_loss"]
#     legit_volume = fraud_legit[0]["legit_volume"]

#     # 4️⃣ Hourly Distribution
#     hourly_distribution = list(collection.aggregate([
#         {
#             "$group": {
#                 "_id": "$hour",
#                 "count": {"$sum": 1}
#             }
#         },
#         {"$sort": {"_id": 1}}
#     ]))

#     # 5️⃣ Daily Activity (Last 7 Days)
#     seven_days_ago = datetime.utcnow() - timedelta(days=7)

#     daily_activity = list(collection.aggregate([
#     {
#         "$group": {
#             "_id": {"$dayOfMonth": "$timestamp"},
#             "count": {"$sum": 1}
#         }
#     },
#     {"$sort": {"_id": 1}}
# ]))


#     return {
#         "volume_data": volume_data,
#         "channel_distribution": channel_distribution,
#         "fraud_loss": fraud_loss,
#         "legit_volume": legit_volume,
#         "hourly_distribution": hourly_distribution,
#         "daily_activity": daily_activity,
#     }




from fastapi import APIRouter
from database import collection
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
def dashboard_analytics():
    """Get complete analytics data for the dashboard"""
    
    # Get total transactions and fraud metrics
    total_stats = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "total_transactions": {"$sum": 1},
                "fraud_transactions": {"$sum": {"$cond": ["$is_fraud", 1, 0]}},
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
            "activity_data": {
                "hourly": [],
                "daily": []
            }
        }
    
    stats = total_stats[0]
    total_transactions = stats["total_transactions"]
    fraud_transactions = stats["fraud_transactions"]
    
    # Calculate fraud rate
    fraud_rate = "0.00"
    if total_transactions > 0:
        fraud_rate = f"{(fraud_transactions / total_transactions * 100):.2f}"
    
    analytics_metrics = {
        "totalTransactions": total_transactions,
        "fraudRate": fraud_rate,
        "fraudLoss": stats["fraud_loss"],
        "legitimateVolume": stats["legit_volume"]
    }
    
    # Transaction Volume by day
    volume_data = list(collection.aggregate([
        {
            "$group": {
                "_id": "$day",
                "volume": {"$sum": "$transaction_amount"}
            }
        },
        {"$sort": {"_id": 1}}
    ]))
    
    volume_by_day_data = [
        {"name": f"Day {item['_id']}", "volume": item["volume"]}
        for item in volume_data
    ]
    
    # Channel Distribution
    channel_stats = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "mobile": {"$sum": "$channel_mobile"},
                "atm": {"$sum": "$channel_atm"},
                "pos": {"$sum": "$channel_pos"},
                "web": {"$sum": "$channel_web"}
            }
        }
    ]))
    
    channel_data = []
    if channel_stats:
        channels = channel_stats[0]
        channel_data = [
            {"name": "Mobile", "value": channels["mobile"], "color": "#3B82F6"},
            {"name": "ATM", "value": channels["atm"], "color": "#10B981"},
            {"name": "POS", "value": channels["pos"], "color": "#F59E0B"},
            {"name": "Web", "value": channels["web"], "color": "#EF4444"},
        ]
    
    # Hourly Distribution
    hourly_data = list(collection.aggregate([
        {
            "$group": {
                "_id": "$hour",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]))
    
    hourly = [
        {"name": f"{item['_id']}:00", "transactions": item["count"]}
        for item in hourly_data
    ]
    
    # Daily Activity
    daily_data = list(collection.aggregate([
        {
            "$group": {
                "_id": "$weekday",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]))
    
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    daily = [
        {"name": day_names[item["_id"] or 0], "transactions": item["count"]}
        for item in daily_data
    ]
    
    return {
        "analytics_metrics": analytics_metrics,
        "volume_by_day_data": volume_by_day_data,
        "channel_data": channel_data,
        "activity_data": {
            "hourly": hourly,
            "daily": daily
        }
    }

@router.get("/summary")
def analytics_summary():
    """Get simplified analytics summary"""
    return dashboard_analytics()

@router.get("/volume-trend")
def volume_trend():
    """Get transaction volume trend by day"""
    volume_data = list(collection.aggregate([
        {
            "$group": {
                "_id": "$day",
                "volume": {"$sum": "$transaction_amount"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]))
    
    return [
        {
            "day": item["_id"],
            "volume": item["volume"],
            "count": item["count"]
        }
        for item in volume_data
    ]

@router.get("/channel-breakdown")
def channel_breakdown():
    """Get detailed channel breakdown"""
    channel_stats = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "mobile": {"$sum": "$channel_mobile"},
                "atm": {"$sum": "$channel_atm"},
                "pos": {"$sum": "$channel_pos"},
                "web": {"$sum": "$channel_web"},
                "total": {"$sum": 1}
            }
        }
    ]))
    
    if not channel_stats:
        return {"mobile": 0, "atm": 0, "pos": 0, "web": 0, "total": 0}
    
    stats = channel_stats[0]
    total = stats["total"]
    
    return {
        "mobile": {"count": stats["mobile"], "percentage": (stats["mobile"]/total*100) if total > 0 else 0},
        "atm": {"count": stats["atm"], "percentage": (stats["atm"]/total*100) if total > 0 else 0},
        "pos": {"count": stats["pos"], "percentage": (stats["pos"]/total*100) if total > 0 else 0},
        "web": {"count": stats["web"], "percentage": (stats["web"]/total*100) if total > 0 else 0},
        "total": total
    }