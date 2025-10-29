from pymongo import MongoClient

client = MongoClient("mongodb+srv://backend_user:aBWmEIMJPz3yLIgq@cluster0.epdt22n.mongodb.net/?appName=Cluster0")
db = client["bfsidata"]
collection = db["transactions"]
