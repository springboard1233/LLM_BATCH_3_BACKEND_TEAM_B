from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

db_client = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
db_collection = os.getenv("COLLECTION_NAME")


client = MongoClient(db_client)
db = client[db_name]
collection = db[db_collection]