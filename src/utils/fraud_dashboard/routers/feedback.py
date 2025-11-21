from fastapi import APIRouter, HTTPException
from datetime import datetime
from src.utils.fraud_dashboard.database import get_collection

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("/submit")
async def submit_feedback(payload: dict):
    """
    Submit feedback on a prediction.
    
    Expected payload:
    {
        "prediction_id": "string",
        "actual_status": "Fraud" or "Legit"
    }
    """
    try:
        # Validate required fields
        if "prediction_id" not in payload:
            raise HTTPException(status_code=400, detail="prediction_id is required")
        
        if "actual_status" not in payload:
            raise HTTPException(status_code=400, detail="actual_status is required")
        
        # Validate actual_status values
        valid_statuses = ["Fraud", "Legit", "fraud", "legit"]
        if payload["actual_status"] not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"actual_status must be one of: {valid_statuses}"
            )
        
        # Normalize status to lowercase for consistency
        normalized_status = payload["actual_status"].lower()
        
        # Create feedback document
        feedback_doc = {
            "prediction_id": payload["prediction_id"],
            "actual_status": normalized_status,
            "submitted_at": datetime.utcnow(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to MongoDB
        result = collection.insert_one(feedback_doc)
        
        # Return success response
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": str(result.inserted_id),
            "data": {
                "prediction_id": feedback_doc["prediction_id"],
                "actual_status": feedback_doc["actual_status"],
                "submitted_at": feedback_doc["submitted_at"].isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {str(e)}")

@router.get("/stats")
async def get_feedback_stats():
    """
    Get feedback statistics - count of fraud vs legit feedback
    """
    try:
        # Aggregate feedback stats
        pipeline = [
            {
                "$group": {
                    "_id": "$actual_status",
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "status": "$_id",
                    "count": 1
                }
            }
        ]
        
        stats = list(collection.aggregate(pipeline))
        
        # Convert to dictionary for easier frontend consumption
        feedback_stats = {"fraud": 0, "legit": 0}
        for stat in stats:
            feedback_stats[stat["status"]] = stat["count"]
        
        return {
            "status": "success",
            "data": feedback_stats,
            "total_feedback": sum(feedback_stats.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")