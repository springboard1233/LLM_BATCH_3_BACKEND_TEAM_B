import pandas as pd
from pymongo import MongoClient
import os
import sys
from dotenv import load_dotenv
load_dotenv()

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
DATABASE_NAME = "bfsidata"
COLLECTION_NAME = "transactions"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PROCESSED_FILE_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "transactions_processed.csv")


def connect_to_mongo():
    """Establishes connection to MongoDB and returns the collection object."""
    try:
        print(f"Connecting to MongoDB Atlas cluster...")
        
        client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=30000)
        
        client.admin.command('ping')
        print("MongoDB connection successful.")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        return collection, client
    except Exception as e:
        print(f"ERROR: Could not connect to MongoDB. Check connection string, password, and Network Access IPs.")
        print(f"Details: {e}")
        sys.exit(1) 

def load_data_from_csv():
    
    if not os.path.exists(PROCESSED_FILE_PATH):
        print(f"ERROR: Processed file not found at {PROCESSED_FILE_PATH}")
        print("This script expects the file here. Please check if 'data/processed/transactions_processed.csv' exists.")
        print("Please run the Member 1 & 2 scripts first, or check your git pull.")
        sys.exit(1)
        
    print(f"Loading data from {PROCESSED_FILE_PATH}...")
    df = pd.read_csv(PROCESSED_FILE_PATH)
    
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except Exception as e:
        print(f"ERROR: Failed to convert 'timestamp' column. Check the CSV format.")
        print(f"Details: {e}")
        sys.exit(1)
        
    print(f"Loaded {len(df)} records from CSV.")
    return df

def insert_data_to_collection(collection, df):
    """Clears the collection and inserts new data from the DataFrame."""
    try:
        print("Converting DataFrame to records...")
        records = df.to_dict('records')

        print(f"Clearing old data from '{COLLECTION_NAME}' collection...")
        collection.delete_many({})
        
        print(f"Inserting {len(records)} new records into MongoDB...")
        result = collection.insert_many(records)
        
        print("\n--- SUCCESS! ---")
        print(f"Inserted {len(result.inserted_ids)} documents.")
        print(f"Database:   {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        
    except Exception as e:
        print(f"ERROR: During data insertion.")
        print(f"Details: {e}")

def main():
    
    if "<password>" in MONGO_CONNECTION_STRING:
        print("="*50)
        print("ERROR: SCRIPT NOT RUN")
        print("Please edit 'src/utils/load_to_mongo.py' and replace")
        print("'<password>' and your cluster host in the")
        print("MONGO_CONNECTION_STRING variable.")
        print("="*50)
        return

    collection, client = connect_to_mongo()
    df = load_data_from_csv()
    insert_data_to_collection(collection, df)
    
    client.close()
    print("MongoDB connection closed.")

if __name__ == "__main__":
    main()

