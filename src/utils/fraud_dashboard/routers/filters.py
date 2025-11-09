# from fastapi import APIRouter
# from database import collection
# from datetime import datetime

# router = APIRouter(prefix="/filter")

# @router.get("/transactions")
# def filter_transactions(
#     start_date: str = None,
#     end_date: str = None,
#     channel: str = None
# ):
#     query = {}

#     if start_date and end_date:
#         query["timestamp"] = {
#             "$gte": datetime.fromisoformat(start_date),
#             "$lte": datetime.fromisoformat(end_date)
#         }

#     if channel:
#         query[channel] = 1

#     data = list(collection.find(query, {"_id": 0}))
#     return data
# This is the complete, corrected code for:
# src/utils/fraud_dashboard/routers/filters.py

import sys
import os
from fastapi import APIRouter
from datetime import datetime

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

router = APIRouter(prefix="/filter")

# --- THIS IS NOW CORRECT ---
# We CALL the function to get the 'transactions' collection
try:
    collection = get_collection("transactions")
except Exception as e:
    print(f"CRITICAL ERROR in filters.py: Could not get 'transactions' collection. {e}")
    collection = None
# ---------------------------

@router.get("/transactions")
def filter_transactions(
    start_date: str = None,
    end_date: str = None,
    channel: str = None
):
    if collection is None:
        return {"error": "Database connection failed"}
        
    query = {}

    if start_date and end_date:
        query["timestamp"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }

    if channel:
        # --- THIS LOGIC IS NOW FIXED ---
        # It now correctly queries fields like 'channel_atm' or 'channel_mobile'
        channel_field = f"channel_{channel.lower()}"
        query[channel_field] = 1
        # -------------------------------

    data = list(collection.find(query, {"_id": 0}))
    return data