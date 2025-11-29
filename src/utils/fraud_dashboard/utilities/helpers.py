from ..database import db

def get_db_last_update():
    meta = db["meta"].find_one({"_id": "last_update"})
    return meta["timestamp"] if meta else None

import os
import joblib

def get_model_feature_importance(project_root):
    """
    Loads the trained model and extracts feature importance scores.
    Returns a dictionary mapping feature names to their importance.
    """
    try:
        # Define the correct path to your model file
        model_path = os.path.join(project_root, "models", "random_forest_model.pkl")
        
        # Load the model
        model = joblib.load(model_path)

      
        feature_names = [
            "kyc_verified",
            "account_age_days",
            "transaction_amount",
            "hour",
            "day",
            "weekday",
            "channel_atm",
            "channel_mobile",
            "channel_pos",
            "channel_web",
            "avg_txn_amount_7d",
            "txn_count_7d",
            "failed_txn_count_7d",
            "max_txn_amount_30d",
            "account_velocity_24h",
            "ip_country_risk_score"
        ]

       
        importances = model.feature_importances_

       
        feature_importance_dict = sorted(
            [{"feature": name, "importance": round(score, 4)} for name, score in zip(feature_names, importances)],
            key=lambda x: x["importance"],
            reverse=True
        )

        return feature_importance_dict

    except FileNotFoundError:
        print(f"Error: Model file not found at {model_path}")
        return []
    except Exception as e:
        print(f"An error occurred while getting feature importance: {e}")
        return []