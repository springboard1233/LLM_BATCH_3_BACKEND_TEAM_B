# src/utils/fraud_dashboard/alert_service.py
from datetime import datetime
from typing import Dict, Any, List
from database import get_collection  # use your database helper

ALERT_COLLECTION_NAME = "fraud_alerts"

def save_alert(transaction_id: str, customer_id: str, risk_score: float, reasons: List[str], details: List[Dict[str, Any]]):
    """
    Persist an alert document to MongoDB (collection: fraud_alerts).
    """
    try:
        collection = get_collection(ALERT_COLLECTION_NAME)
        alert_doc = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "risk_score": float(risk_score),
            "reasons": reasons,          # simple list of codes
            "details": details,          # structured reasons with severity and messages
            "created_at": datetime.utcnow()
        }
        collection.insert_one(alert_doc)
        return True
    except Exception as e:
        # do not crash the API if alert saving fails; log and continue
        print(f"ERROR: failed to save alert to MongoDB: {e}")
        return False
