# from fastapi import APIRouter
# from database import collection

# router = APIRouter(prefix="/insights")

# @router.get("/transaction_amounts")
# def amount_insights():
#     pipeline = [
#         {
#             "$group": {
#                 "_id": None,
#                 "avg_amount": {"$avg": "$transaction_amount"},
#                 "max_amount": {"$max": "$transaction_amount"},
#                 "min_amount": {"$min": "$transaction_amount"},
#             }
#         }
#     ]
#     data = list(collection.aggregate(pipeline))[0]
#     return data
# This is the complete, corrected code for:
# src/utils/fraud_dashboard/routers/insights.py

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

router = APIRouter(prefix="/insights")

# --- THIS IS NOW CORRECT ---
# We CALL the function to get the 'transactions' collection
try:
    collection = get_collection("transactions")
except Exception as e:
    print(f"CRITICAL ERROR in insights.py: Could not get 'transactions' collection. {e}")
    collection = None
# ---------------------------

@router.get("/transaction_amounts")
def amount_insights():
    if collection is None:
        return {"error": "Database connection failed"}
        
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
    
    try:
        data = list(collection.aggregate(pipeline))[0]
        return data
    except IndexError:
        return {"error": "No data found"}
    except Exception as e:
        return {"error": str(e)}