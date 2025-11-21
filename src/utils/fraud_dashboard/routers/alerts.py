# from fastapi import APIRouter
# from database import collection
# from utils import convert_objectid

# router = APIRouter(prefix="/alerts")

# @router.get("/suspicious")
# def suspicious_transactions():
#     pipeline = [
#         {"$match": {"transaction_amount": {"$gt": 0.9}}},
#         {"$sort": {"transaction_amount": -1}},
#         {"$limit": 10}
#     ]
#     result = list(collection.aggregate(pipeline))
#     return convert_objectid(result)
# This is the complete, corrected code for:
# src/utils/fraud_dashboard/routers/alerts.py

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

# --- THESE IMPORTS ARE NOW CORRECT ---
# It imports the FUNCTION from the correct 'utilities' folder
from src.utils.fraud_dashboard.database import get_collection
from src.utils.fraud_dashboard.utils import convert_objectid
# -----------------------------------

router = APIRouter(prefix="/alerts")

# --- THIS IS NOW CORRECT ---
# We CALL the function to get the 'transactions' collection
try:
    collection = get_collection("transactions")
except Exception as e:
    print(f"CRITICAL ERROR in alerts.py: Could not get 'transactions' collection. {e}")
    collection = None
# ---------------------------

@router.get("/suspicious")
def suspicious_transactions():
    if collection is None:
        return {"error": "Database connection failed"}
        
    pipeline = [
        {"$match": {"transaction_amount": {"$gt": 0.9}}}, # Assuming 0.9 is a scaled value
        {"$sort": {"transaction_amount": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return convert_objectid(result)