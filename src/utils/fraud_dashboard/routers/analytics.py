# from fastapi import APIRouter
# from database import collection

# router = APIRouter(prefix="/analytics")

# @router.get("/fraud-trend")
# def fraud_trend():
#     """Get fraud trends over time"""
#     pipeline = [
#         {
#             "$group": {
#                 "_id": { 
#                     "day": "$day",
#                     "year": {"$year": "$timestamp"},
#                     "month": {"$month": "$timestamp"}
#                 },
#                 "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}},
#                 "total": {"$sum": 1},
#                 "fraud_amount": {"$sum": {"$cond": ["$is_fraud", "$transaction_amount", 0]}}
#             }
#         },
#         {"$sort": {"_id.day": 1}}
#     ]
#     return list(collection.aggregate(pipeline))

# @router.get("/fraud-by-channel")
# def fraud_by_channel():
#     """Get fraud distribution by channel"""
#     pipeline = [
#         {
#             "$group": {
#                 "_id": None,
#                 "mobile_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_mobile", 1]}]}, 1, 0]}},
#                 "atm_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_atm", 1]}]}, 1, 0]}},
#                 "pos_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_pos", 1]}]}, 1, 0]}},
#                 "web_fraud": {"$sum": {"$cond": [{"$and": [{"$eq": ["$is_fraud", 1]}, {"$eq": ["$channel_web", 1]}]}, 1, 0]}},
#                 "mobile_total": {"$sum": "$channel_mobile"},
#                 "atm_total": {"$sum": "$channel_atm"},
#                 "pos_total": {"$sum": "$channel_pos"},
#                 "web_total": {"$sum": "$channel_web"}
#             }
#         }
#     ]
#     return list(collection.aggregate(pipeline))

# @router.get("/fraud-loss")
# def fraud_loss():
#     """Get total fraud loss amount"""
#     pipeline = [
#         {
#             "$group": {
#                 "_id": None,
#                 "total_fraud_loss": {"$sum": {"$cond": ["$is_fraud", "$transaction_amount", 0]}},
#                 "avg_fraud_amount": {"$avg": {"$cond": ["$is_fraud", "$transaction_amount", None]}},
#                 "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}}
#             }
#         }
#     ]
#     return list(collection.aggregate(pipeline))
# @router.get("/dashboard")
# def dashboard():
#     # Add your dashboard logic here
#     # For example, you might want to return aggregated data from multiple endpoints
#     return {
#         "fraud_trend": fraud_trend(),
#         "fraud_by_channel": fraud_by_channel(),
#         "fraud_loss": fraud_loss()
#     }
# This is the complete, corrected code for:
# src/utils/fraud_dashboard/routers/analytics.py

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

@router.get("/fraud-trend")
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

@router.get("/fraud-by-channel")
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

@router.get("/fraud-loss")
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
    # This will now work
    if collection is None:
        return {"error": "Database connection failed"}
    return {
        "fraud_trend": fraud_trend(),
        "fraud_by_channel": fraud_by_channel(),
        "fraud_loss": fraud_loss()
    }