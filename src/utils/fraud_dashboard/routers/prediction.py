import sys
import os
import pandas as pd
import joblib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
import json
from redis.client import Redis

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.fraud_dashboard.database import get_collection
from src.utils.fraud_dashboard.cache import get_redis_client, get_from_cache, set_in_cache

router = APIRouter(
    prefix="/prediction",
    tags=["Prediction Engine"]
)

try:
    model = joblib.load("models/random_forest_model.pkl")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load 'models/random_forest_model.pkl'. {e}")
    model = None

model_metrics = {
    "accuracy_score": 0.9996025068213695,
    "precision_score": 0.9322033898305084,
    "recall_score": 0.8148148148148148,
    "f1_score": 0.869281045751634,
    "roc_auc_score": 0.907340051111663
}


class RawTransactionInput(BaseModel):
    customer_id: str
    kyc_verified: int
    account_age_days: int
    transaction_amount: float
    channel: str
    timestamp: str


def transform_features(raw_input: RawTransactionInput) -> Dict:
    try:
        dt = datetime.fromisoformat(raw_input.timestamp)
    except ValueError:
        dt = datetime.strptime(raw_input.timestamp, "%Y-%m-%d %H:%M:%S")
    hour = dt.hour
    day = dt.day
    weekday = dt.weekday()
    channel = raw_input.channel.lower()
    channel_atm = 1 if channel == 'atm' else 0
    channel_mobile = 1 if channel == 'mobile' else 0
    channel_pos = 1 if channel == 'pos' else 0
    channel_web = 1 if channel == 'web' else 0
    high_amount_flag = 1 if raw_input.transaction_amount > 10000 else 0
    is_night = 1 if 0 <= hour <= 6 else 0
    is_weekend = 1 if weekday >= 5 else 0
    avg_txn_per_customer = 0.12  # PLACEHOLDER
    txns_count_per_customer = 5    # PLACEHOLDER
    amt_deviation = 0.03         # PLACEHOLDER
    engineered_features = {
        "kyc_verified": raw_input.kyc_verified,
        "account_age_days": raw_input.account_age_days,
        "transaction_amount": raw_input.transaction_amount,
        "hour": hour, "day": day, "weekday": weekday,
        "channel_atm": channel_atm, "channel_mobile": channel_mobile,
        "channel_pos": channel_pos, "channel_web": channel_web,
        "avg_txn_per_customer": avg_txn_per_customer,
        "txns_count_per_customer": txns_count_per_customer,
        "amt_deviation": amt_deviation,
        "high_amount_flag": high_amount_flag,
        "is_night": is_night, "is_weekend": is_weekend
    }
    return engineered_features

# 5. YOUR API ENDPOINTS
@router.get("/metrics")
def get_metrics(cache: Redis = Depends(get_redis_client)):
    cache_key = "model_metrics"
    cached_data = get_from_cache(cache, cache_key)
    if cached_data:
        return json.loads(cached_data)
    set_in_cache(cache, cache_key, json.dumps(model_metrics), ttl_seconds=3600)
    return model_metrics


@router.post("/predict")
def predict_and_save(transaction: RawTransactionInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model 'random_forest_model.pkl' is not loaded.")
    try:
        engineered_features = transform_features(transaction)
        feature_order = [
            'kyc_verified', 'account_age_days', 'transaction_amount', 'hour', 'day',
            'weekday', 'channel_atm', 'channel_mobile', 'channel_pos',
            'channel_web', 'avg_txn_per_customer', 'txns_count_per_customer',
            'amt_deviation', 'high_amount_flag', 'is_night', 'is_weekend'
        ]
        input_df = pd.DataFrame([engineered_features])[feature_order]
        prediction_raw = model.predict(input_df)
        prediction_proba = model.predict_proba(input_df)
        is_fraud = bool(prediction_raw[0])
        risk_score = float(prediction_proba[0][1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

   
    prediction_record = transaction.dict()
    prediction_record["is_fraud"] = is_fraud
    prediction_record["risk_score"] = risk_score
    prediction_record["processed_at"] = datetime.now() # Use processed_at for the index
    
    try:
        
        prediction_collection = get_collection("predictions")
       
        prediction_collection.create_index("processed_at")
        prediction_collection.create_index("risk_score")
       
        prediction_collection.insert_one(prediction_record)

    except Exception as e:
        print(f"ERROR: Failed to save to MongoDB. {e}")
    
    return {"is_fraud": is_fraud, "risk_score": risk_score}