# This is the complete, corrected code for:
# src/utils/utilities/database.py

import sys
import os
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

# --- PATH FIX for imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- END OF PATH FIX ---

# Load .env file if it exists (optional - environment variables from Docker will take precedence)
# Try multiple locations for .env file
dotenv_paths = [
    os.path.join(project_root, ".env"),
    os.path.join(os.getcwd(), ".env"),
    ".env"
]
for dotenv_path in dotenv_paths:
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        break
else:
    # In Docker, environment variables are set directly, so .env is optional
    load_dotenv()  # This will still check for .env in current directory, but won't fail if missing

# Get environment variables (Docker environment variables take precedence)
mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("MONGO_DB_NAME")

if not mongo_uri or not db_name:
    print("CRITICAL ERROR: MONGO_URI or MONGO_DB_NAME environment variables not set")
    print(f"MONGO_URI: {'Set' if mongo_uri else 'NOT SET'}")
    print(f"MONGO_DB_NAME: {'Set' if db_name else 'NOT SET'}")
    print("Please set these environment variables or create a .env file")
    sys.exit(1) # Exit if env variables are not set

# Initialize MongoDB connection
client = None
db = None

try:
    print(f"Attempting to connect to MongoDB: {mongo_uri.split('@')[1] if '@' in mongo_uri else mongo_uri}")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.server_info()  # Will raise exception if cannot connect
    db = client[db_name]
    print(f"✓ MongoDB client initialized successfully.")
    print(f"✓ Connected to database: {db_name}")
    print(f"✓ Available collections: {db.list_collection_names()}")
except Exception as e:
    print(f"CRITICAL ERROR connecting to MongoDB: {e}")
    print(f"MONGO_URI used: {mongo_uri}")
    print(f"MONGO_DB_NAME used: {db_name}")
    client = None
    db = None

def get_database() -> Database:
    if db is None:
        raise Exception("Database not initialized.")
    return db

def get_collection(collection_name: str) -> Collection:
    db = get_database()
    return db[collection_name]