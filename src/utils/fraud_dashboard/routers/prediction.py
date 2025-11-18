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

# -------------------------------------------
# FIX PROJECT ROOT AND IMPORT PATHS
# -------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# FIX IMPORTS
from src.utils.fraud_dashboard.database import get_collection
from src.utils.fraud_dashboard.cache import (
    get_redis_client, get_from_cache, set_in_cache
)

router = APIRouter(
    prefix="/prediction",
    tags=["Prediction Engine"]
)

# -------------------------------------------
# FIX MODEL PATH (ABSOLUTE PATH)
# -------------------------------------------
model_path = os.path.join(project_root, "models", "random_forest_model.pkl")

try:
    model = joblib.load(model_path)
    print("Random Forest model loaded successfully from:", model_path)
except Exception as e:
    print(f"CRITICAL ERROR loading model. {e}")
    model = None


model_metrics = {
    "accuracy_score": 0.913,
    "precision_score": 0.33333,
    "recall_score": 0.0349,
    "f1_score": 0.0625,
}


# -------------------------------------------
# INPUT SCHEMA
# -------------------------------------------
class RawTransactionInput(BaseModel):
    customer_id: str
    kyc_verified: int
    account_age_days: int
    transaction_amount: float
    channel: str
    timestamp: str


# -------------------------------------------
# FEATURE ENGINEERING
# -------------------------------------------
def transform_features(raw_input: RawTransactionInput) -> Dict:
    dt = datetime.fromisoformat(raw_input.timestamp)

    hour = dt.hour
    day = dt.day
    weekday = dt.weekday()

    channel = raw_input.channel.lower()
    engineered_features = {
        "kyc_verified": raw_input.kyc_verified,
        "account_age_days": raw_input.account_age_days,
        "transaction_amount": raw_input.transaction_amount,
        "hour": hour,
        "day": day,
        "weekday": weekday,
        "channel_atm": 1 if channel == 'atm' else 0,
        "channel_mobile": 1 if channel == 'mobile' else 0,
        "channel_pos": 1 if channel == 'pos' else 0,
        "channel_web": 1 if channel == 'web' else 0,
        "avg_txn_per_customer": 0.12,
        "txns_count_per_customer": 5,
        "amt_deviation": 0.03,
        "high_amount_flag": 1 if raw_input.transaction_amount > 10000 else 0,
        "is_night": 1 if 0 <= hour <= 6 else 0,
        "is_weekend": 1 if weekday >= 5 else 0,
    }
    return engineered_features


# -------------------------------------------
# GEMINI LLM EXPLANATION
# -------------------------------------------
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

def generate_fraud_explanation(raw_input, engineered_features, is_fraud, risk_score):
    ml_reason = engineered_features.get("ml_reason")
    rule_reasons = engineered_features.get("rule_reasons", [])

    ml_reason_text = ml_reason if ml_reason else ""
    rule_reasons_text = "\n".join(f"- {r}" for r in rule_reasons) if rule_reasons else "None"

    prompt = f"""
You are an experienced fraud analyst. Create a detailed yet concise explanation
based only on the facts below. Never invent additional data.

Summary:
- Final Verdict: {is_fraud}
- Risk Score: {risk_score:.2f}
- ML Reason: "{ml_reason_text if ml_reason_text else "None"}"
- Rule Reasons:
{rule_reasons_text}

Response requirements:
1. Provide a headline sentence summarizing the outcome and confidence.
2. Add a "Key Drivers" section with bullet points describing every ML or rule
   signal that actually triggered. Mention concrete values (amount, channel,
   KYC status, hour, account age) when relevant. If nothing triggered, state
   that explicitly.
3. Add an "Assessment" paragraph (2 sentences max) explaining why the verdict
   aligns with the risk score and how the rules/ML agree or conflict.
4. Add a "Next Actions" section with 1–2 actionable steps (e.g., request
   verification, monitor account). If verdict is False and no indicators fired,
   state “No additional action required.”
5. Keep the whole response under roughly 180 words.

Strict rules:
- Do not change the verdict or risk score values.
- Do not reference internal system names or models.
- Only use the provided reasons and transaction context.
"""

    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"LLM explanation failed: {e}"


# -------------------------------------------
# METRICS ENDPOINT
# -------------------------------------------
@router.get("/metrics")
def get_metrics(cache: Redis = Depends(get_redis_client)):
    cache_key = "model_metrics"
    cached_data = get_from_cache(cache, cache_key)

    if cached_data:
        return json.loads(cached_data)

    set_in_cache(cache, cache_key, json.dumps(model_metrics), ttl_seconds=3600)
    return model_metrics

def apply_business_rules(transaction, engineered_features):
    """
    Returns:
    - rule_triggered (bool)
    - reasons (list of strings)
    - rule_score (0–1)
    """

    reasons = []
    rule_triggered = False
    score = 0.0

    amt = transaction.transaction_amount
    kyc = transaction.kyc_verified
    channel = transaction.channel.lower()
    age = transaction.account_age_days
    hour = engineered_features["hour"]

    # Rule 1: High amount deviation (simple threshold)
    if amt > max(5 * engineered_features["avg_txn_per_customer"], 1000):

        rule_triggered = True
        score += 0.4
        reasons.append("Amount is more than 5× usual customer pattern.")

    # Rule 2: No KYC + high risk channel
    if kyc == 0 and channel in ["international", "web"]:
        rule_triggered = True
        score += 0.3
        reasons.append("Unverified customer attempting risky channel transaction.")

    # Rule 3: Odd hours transaction (2AM–4AM)
    if 2 <= hour <= 4:
        rule_triggered = True
        score += 0.2
        reasons.append("Transaction made at unusual time (2AM–4AM).")

    # Rule 4: New accounts making sudden high-value payments
    if age < 5 and amt > 10000:
        rule_triggered = True
        score += 0.3
        reasons.append("New account attempting high-value transaction.")

    return rule_triggered, reasons, min(score, 1.0)

# -------------------------------------------
# PREDICTION ENDPOINT
# -------------------------------------------
@router.post("/predict")
def predict_and_save(transaction: RawTransactionInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    # 1. Feature engineering
    engineered_features = transform_features(transaction)

    # 2. ML prediction
    feature_order = [
        'kyc_verified', 'account_age_days', 'transaction_amount', 'hour', 'day',
        'weekday', 'channel_atm', 'channel_mobile', 'channel_pos',
        'channel_web', 'avg_txn_per_customer', 'txns_count_per_customer',
        'amt_deviation', 'high_amount_flag', 'is_night', 'is_weekend'
    ]
    input_df = pd.DataFrame([engineered_features])[feature_order]

    prediction_raw = model.predict(input_df)
    prediction_proba = model.predict_proba(input_df)

    ml_fraud = bool(prediction_raw[0])
    ml_score = float(prediction_proba[0][1])

    # 3. Apply business rules
    rule_triggered, rule_reasons, rule_score = apply_business_rules(
        transaction,
        engineered_features
    )

    # 4. Hybrid final decision
    final_score = max(ml_score, rule_score)
    final_fraud = final_score >= 0.50


    # 5. Collect reasons from ML + rules
    reasons = []
    if ml_fraud:
        reasons.append("ML model predicted high fraud probability.")
    reasons.extend(rule_reasons)

    # 6. Generate LLM explanation
    explanation = generate_fraud_explanation(
        transaction.dict(),
        engineered_features,
        final_fraud,
        final_score
    )

    # 7. Save prediction
    record = transaction.dict()
    record["is_fraud"] = final_fraud
    record["risk_score"] = final_score
    record["ml_reason"] = ("ML model predicted high fraud probability." if ml_fraud else None)
    record["rule_reasons"] = rule_reasons
    record["combined_reasons"] = reasons

    record["processed_at"] = datetime.now()
    record["explanation"] = explanation

    predictions = get_collection("predictions")
    predictions.insert_one(record)

    # 8. Save fraud alerts ONLY if flagged
    if final_fraud:
        alerts = get_collection("fraud_alerts")
        alerts.insert_one({
        "transaction_id": transaction.customer_id + "_" + transaction.timestamp,
        "customer_id": transaction.customer_id,
        "risk_score": final_score,
        "ml_reason": "ML model predicted high fraud probability." if ml_fraud else None,
        "rule_reasons": rule_reasons,
        "timestamp": datetime.now(),
        })


    return {
    "is_fraud": final_fraud,
    "risk_score": final_score,
    "ml_reason": "ML model predicted high fraud probability." if ml_fraud else None,
    "rule_reasons": rule_reasons,
    "combined_reasons": reasons,
    "explanation": explanation,
    }

