from ..database import db

def get_db_last_update():
    meta = db["meta"].find_one({"_id": "last_update"})
    return meta["timestamp"] if meta else None
