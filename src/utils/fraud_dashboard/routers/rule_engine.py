# src/utils/fraud_dashboard/rule_engine.py
from typing import Dict, List, Tuple

# Example config / thresholds (tune these to your data)
AVG_TXN_MULTIPLIER_THRESHOLD = 5.0   # > 5x average => suspicious
ODD_HOUR_START = 2
ODD_HOUR_END = 4
HIGH_RISK_RULE_SEVERITY = "high"
MEDIUM_RISK_RULE_SEVERITY = "medium"
LOW_RISK_RULE_SEVERITY = "low"

def evaluate_rules(raw_input: Dict, engineered_features: Dict, customer_profile: Dict = None) -> Tuple[List[str], List[Dict]]:
    """
    Evaluate business rules and return:
      - list of triggered rule keys (strings)
      - list of structured triggers with reason and severity
    """
    triggers = []
    triggered_details = []

    amount = raw_input.get("transaction_amount", engineered_features.get("transaction_amount"))
    hour = engineered_features.get("hour")
    channel = (raw_input.get("channel") or "").lower()
    kyc = raw_input.get("kyc_verified")
    account_age = raw_input.get("account_age_days", 0)

    # Placeholder: if you have historical avg per customer, pass via customer_profile
    avg_txn_customer = None
    if customer_profile and "avg_txn_amount" in customer_profile:
        avg_txn_customer = customer_profile["avg_txn_amount"]

    # Rule 1: Very large transaction vs average (if avg known)
    if avg_txn_customer and avg_txn_customer > 0:
        if amount > avg_txn_customer * AVG_TXN_MULTIPLIER_THRESHOLD:
            triggers.append("HIGH_AMOUNT_VS_AVG")
            triggered_details.append({
                "rule": "HIGH_AMOUNT_VS_AVG",
                "reason": f"Transaction amount {amount} is > {AVG_TXN_MULTIPLIER_THRESHOLD}x customer's avg {avg_txn_customer}",
                "severity": HIGH_RISK_RULE_SEVERITY
            })

    # Rule 2: channel international + KYC not verified
    if channel in ("international", "intl", "wire") and (kyc == 0 or kyc == "No" or kyc is False):
        triggers.append("INTERNATIONAL_NO_KYC")
        triggered_details.append({
            "rule": "INTERNATIONAL_NO_KYC",
            "reason": "International channel with KYC not verified",
            "severity": HIGH_RISK_RULE_SEVERITY
        })

    # Rule 3: odd hour transaction (2AM-4AM)
    if isinstance(hour, int) and (ODD_HOUR_START <= hour <= ODD_HOUR_END):
        triggers.append("ODD_HOUR_TXN")
        triggered_details.append({
            "rule": "ODD_HOUR_TXN",
            "reason": f"Transaction at odd hour: {hour}:00",
            "severity": MEDIUM_RISK_RULE_SEVERITY
        })

    # Rule 4: very new account making transaction
    if account_age is not None and account_age < 7 and amount > 1000:
        triggers.append("NEW_ACCOUNT_HIGH_AMOUNT")
        triggered_details.append({
            "rule": "NEW_ACCOUNT_HIGH_AMOUNT",
            "reason": f"Account age {account_age} days and amount {amount} is high for new account",
            "severity": MEDIUM_RISK_RULE_SEVERITY
        })

    # Rule 5: high amount absolute threshold
    if amount is not None and amount > 200000:  # absolute extreme
        triggers.append("ABSOLUTE_HIGH_AMOUNT")
        triggered_details.append({
            "rule": "ABSOLUTE_HIGH_AMOUNT",
            "reason": f"Transaction amount {amount} exceeds absolute threshold",
            "severity": HIGH_RISK_RULE_SEVERITY
        })

    # You can append more rules here.
    return triggers, triggered_details
