import sys
import os
import pandas as pd
import joblib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any
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
from src.utils.fraud_dashboard.utils import convert_objectid

# -------------------------------------------
# OPTIONAL: RULE ENGINE & ALERT SERVICE
# -------------------------------------------
try:
    from . import rule_engine  # src.utils.fraud_dashboard.rule_engine
except Exception:
    rule_engine = None  # type: ignore

try:
    from . import alert_service  # src.utils.fraud_dashboard.alert_service
except Exception:
    alert_service = None  # type: ignore


router = APIRouter(
    prefix="/prediction",
    tags=["Prediction Engine"]
)

# -------------------------------------------
# MODEL LOADING
# -------------------------------------------
model_path = os.path.join(project_root, "models", "random_forest_model.pkl")

try:
    model = joblib.load(model_path)
    print("Random Forest model loaded successfully from:", model_path)
except Exception as e:
    print(f"CRITICAL ERROR loading model. {e}")
    model = None

try:
    predictions_collection = get_collection("predictions")
except Exception as e:
    print(f"CRITICAL ERROR in prediction.py: Could not get 'predictions' collection. {e}")
    predictions_collection = None


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
# GEMINI LLM EXPLANATION (FALLBACK)
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

Response requirements (PLAIN TEXT ONLY):
1) Start with one sentence summarizing the outcome and confidence.
2) Add a "Key Drivers:" section in plain text (no bullet symbols). List each driver on a new line starting with a dash (-), but do not use markdown or asterisks.
3) Add an "Assessment:" section (max two sentences) explaining why the verdict matches the risk score and how rules/ML agree or conflict.
4) Add a "Next Actions:" section with 1–2 concrete actions. If verdict is False and no indicators fired, say "No additional action required."
5) Do NOT use markdown formatting, headings, asterisks, or numbered/bullet lists. Plain text only.

Strict rules:
- Do not change the verdict or risk score values.
- Do not reference internal system names or models.
- Only use the provided reasons and transaction context.
"""


    try:
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        # hard-strip any stray markdown bullets if model still adds them
        text = text.replace("*", "")
        return text
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


# -------------------------------------------
# LEGACY BUSINESS RULES (KEPT + COMBINED WITH RULE ENGINE)
# -------------------------------------------
def apply_business_rules(transaction: RawTransactionInput, engineered_features: Dict):
    """
    Returns:
    - rule_triggered (bool)
    - reasons (list of strings)
    - rule_score (0–1)
    """

    reasons: List[str] = []
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
    if predictions_collection is None:
        raise HTTPException(status_code=503, detail="Database is not available.")

    # 1. Feature engineering
    engineered_features = transform_features(transaction)
    payload = transaction.dict()

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

    # 3. Legacy business rules
    legacy_triggered, legacy_rule_reasons, legacy_rule_score = apply_business_rules(
        transaction,
        engineered_features
    )

    # 4. New rule_engine rules
    rule_triggers: List[str] = []
    rule_details: List[Dict[str, Any]] = []
    engine_rule_score = 0.0

    if rule_engine:
        try:
            rule_triggers, rule_details = rule_engine.evaluate_rules(
                raw_input=payload,
                engineered_features=engineered_features,
                customer_profile=None,   # extend later if you have profile
            )

            # derive numeric score from severities
            sev_map = {
                getattr(rule_engine, "HIGH_RISK_RULE_SEVERITY", "high"): 0.5,
                getattr(rule_engine, "MEDIUM_RISK_RULE_SEVERITY", "medium"): 0.3,
                getattr(rule_engine, "LOW_RISK_RULE_SEVERITY", "low"): 0.1,
            }
            for d in rule_details:
                sev = d.get("severity")
                engine_rule_score += sev_map.get(sev, 0.1)

            if engine_rule_score > 1.0:
                engine_rule_score = 1.0
        except Exception as e:
            print(f"ERROR evaluating rule_engine: {e}")
            rule_triggers, rule_details, engine_rule_score = [], [], 0.0

    # 5. Combine rule reasons + scores
    engine_rule_reasons = [d.get("reason", "") for d in rule_details if d.get("reason")]
    rule_reasons: List[str] = legacy_rule_reasons + engine_rule_reasons

    rule_score = max(legacy_rule_score, engine_rule_score)

    # 6. Hybrid final decision
    final_score = max(ml_score, rule_score)
    final_fraud = final_score >= 0.50

    # 7. ML reason + combined reasons
    ml_reason = (
        "ML model predicted high fraud probability."
        if ml_fraud
        else "No ML alerts were triggered."
    )

    # Rule reasons = ONLY actual rule messages (empty list if none)
    # let the frontend decide how to display “no rules”
    rule_reasons = rule_reasons  # already built above

    # Combined reasons = ML + rules
    combined_reasons: List[str] = []
    combined_reasons.append(ml_reason)

    if rule_reasons:
        combined_reasons.extend(rule_reasons)
    else:
        combined_reasons.append("No rule-based alerts were triggered.")

    # 8. Explanation (Gemini, plain text)
    engineered_features_for_llm = dict(engineered_features)
    engineered_features_for_llm["ml_reason"] = ml_reason
    engineered_features_for_llm["rule_reasons"] = rule_reasons

    explanation = generate_fraud_explanation(
        payload,
        engineered_features_for_llm,
        final_fraud,
        final_score
    )

    # 9. Build API result
    result = {
        "is_fraud": final_fraud,
        "risk_score": final_score,
        "ml_reason": ml_reason,
        "rule_reasons": rule_reasons,          # no fake "No rules..." string
        "combined_reasons": combined_reasons,  # ML + rules
        "explanation": explanation,
    }


    # 10. Save prediction record
    record = payload.copy()
    record["is_fraud"] = final_fraud
    record["risk_score"] = final_score
    record["ml_reason"] = ml_reason
    record["rule_reasons"] = rule_reasons
    record["combined_reasons"] = combined_reasons
    record["rule_triggers"] = rule_triggers
    record["rule_details"] = rule_details
    record["processed_at"] = datetime.now()
    record["explanation"] = explanation

    predictions_collection.insert_one(record)

    # 11. Save fraud alert via alert_service when high risk
    try:
        if alert_service and (final_score > 0.75 or final_fraud):
            transaction_id = f"{transaction.customer_id}_{transaction.timestamp}"
            # use rule_triggers if available, else fall back to text rule_reasons
            reasons_for_alert = rule_triggers or rule_reasons
            alert_service.save_alert(
                transaction_id=transaction_id,
                customer_id=transaction.customer_id,
                risk_score=final_score,
                reasons=reasons_for_alert,
                details=rule_details,
            )
    except Exception as e:
        print(f"ERROR: failed to save alert via alert_service: {e}")

    return result


@router.get("/history")
def get_prediction_history(page: int = 1, limit: int = 25):
    if predictions_collection is None:
        raise HTTPException(status_code=503, detail="Database is not available.")

    page = max(page, 1)
    limit = max(1, min(limit, 200))
    skip = (page - 1) * limit

    total = predictions_collection.count_documents({})
    cursor = (
        predictions_collection.find()
        .sort("processed_at", -1)
        .skip(skip)
        .limit(limit)
    )

    records = []
    for doc in cursor:
        doc = convert_objectid(doc)
        raw_id = doc.pop("_id", None)
        if raw_id and "id" not in doc:
            doc["id"] = raw_id

        processed_at = doc.get("processed_at")
        if hasattr(processed_at, "isoformat"):
            doc["processed_at"] = processed_at.isoformat()

        timestamp = doc.get("timestamp")
        if hasattr(timestamp, "isoformat"):
            doc["timestamp"] = timestamp.isoformat()

        records.append(doc)

    return {
        "data": records,
        "page": page,
        "limit": limit,
        "total": total,
        "has_next": skip + len(records) < total,
    }
