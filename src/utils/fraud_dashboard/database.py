# This is the complete, corrected code for:
# src/utils/utilities/database.py

import sys
import os
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

# --- NEW PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=dotenv_path)
# --- END OF NEW PATH FIX ---

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("MONGO_DB_NAME")

if not mongo_uri or not db_name:
    print("CRITICAL ERROR: MONGO_URI or MONGO_DB_NAME not found in .env file")
    sys.exit(1) # Exit if env variables are not set

try:
    client = MongoClient(mongo_uri)
    db = client[db_name]  # This will no longer fail
    print("MongoDB client initialized successfully.")
except Exception as e:
    print(f"CRITICAL ERROR connecting to MongoDB: {e}")
    client = None
    db = None

def get_database() -> Database:
    if db is None:
        raise Exception("Database not initialized.")
    return db

def get_collection(collection_name: str) -> Collection:
    db = get_database()
    return db[collection_name]