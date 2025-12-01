import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from math import floor

from fastapi import APIRouter, Query

# --- NEW PATH FIX ---
# This code manually adds your project's root folder to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 4 levels: routers -> fraud_dashboard -> utils -> src -> ROOT
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- END OF NEW PATH FIX ---

# --- THIS IMPORT IS NOW CORRECT ---
# It imports the FUNCTION from the correct 'utilities' folder
from src.utils.fraud_dashboard.database import get_collection
# -----------------------------------

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# --- THIS IS NOW CORRECT ---
# We CALL the function to get the 'transactions' collection
try:
    collection = get_collection("transactions")
except Exception as e:
    print(
        f"CRITICAL ERROR in analytics.py: Could not get 'transactions' collection. {e}"
    )
    collection = None
# ---------------------------


@router.get("/fraud_trend", tags=["Analytics"])
def fraud_trend():
    """Get fraud trends over time"""
    if collection is None:
        return {"error": "Database connection failed"}

    pipeline = [
        {
            "$group": {
                "_id": {
                    "day": "$day",
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                },
                "fraud_count": {
                    "$sum": {"$cond": ["$is_fraud", 1, 0]}
                },
                "total": {"$sum": 1},
                "fraud_amount": {
                    "$sum": {
                        "$cond": ["$is_fraud", "$transaction_amount", 0]
                    }
                },
            }
        },
        {"$sort": {"_id.day": 1}},
    ]
    return list(collection.aggregate(pipeline))


@router.get("/fraud_by_channel")
def fraud_by_channel():
    """Get fraud distribution by channel"""
    if collection is None:
        return {"error": "Database connection failed"}

    pipeline = [
        {
            "$group": {
                "_id": None,
                "mobile_fraud": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$is_fraud", 1]},
                                    {"$eq": ["$channel_mobile", 1]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "atm_fraud": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$is_fraud", 1]},
                                    {"$eq": ["$channel_atm", 1]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "pos_fraud": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$is_fraud", 1]},
                                    {"$eq": ["$channel_pos", 1]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "web_fraud": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$is_fraud", 1]},
                                    {"$eq": ["$channel_web", 1]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "mobile_total": {"$sum": "$channel_mobile"},
                "atm_total": {"$sum": "$channel_atm"},
                "pos_total": {"$sum": "$channel_pos"},
                "web_total": {"$sum": "$channel_web"},
            }
        }
    ]
    return list(collection.aggregate(pipeline))


@router.get("/fraud_loss")
def fraud_loss():
    """Get total fraud loss amount"""
    if collection is None:
        return {"error": "Database connection failed"}

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_fraud_loss": {
                    "$sum": {"$cond": ["$is_fraud", "$transaction_amount", 0]}
                },
                "avg_fraud_amount": {
                    "$avg": {"$cond": ["$is_fraud", "$transaction_amount", None]}
                },
                "fraud_count": {
                    "$sum": {"$cond": ["$is_fraud", 1, 0]}
                },
            }
        }
    ]
    return list(collection.aggregate(pipeline))


@router.get("/dashboard")
def dashboard():
    """Return aggregated analytics data expected by the frontend dashboard"""
    if collection is None:
        return {"error": "Database connection failed"}

    total_stats = list(
        collection.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "total_transactions": {"$sum": 1},
                        "fraud_transactions": {
                            "$sum": {"$cond": ["$is_fraud", 1, 0]}
                        },
                        "fraud_loss": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$is_fraud", 1]},
                                    "$transaction_amount",
                                    0,
                                ]
                            }
                        },
                        "legit_volume": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$is_fraud", 0]},
                                    "$transaction_amount",
                                    0,
                                ]
                            }
                        },
                    }
                }
            ]
        )
    )

    if not total_stats:
        return {
            "analytics_metrics": {
                "totalTransactions": 0,
                "fraudRate": "0.00",
                "fraudLoss": 0,
                "legitimateVolume": 0,
            },
            "volume_by_day_data": [],
            "channel_data": [],
            "activity_data": {"hourly": [], "daily": []},
        }

    stats = total_stats[0]
    total_transactions = stats.get("total_transactions", 0)
    fraud_transactions = stats.get("fraud_transactions", 0)
    fraud_rate = (
        f"{(fraud_transactions / total_transactions * 100):.2f}"
        if total_transactions > 0
        else "0.00"
    )

    analytics_metrics = {
        "totalTransactions": total_transactions,
        "fraudRate": fraud_rate,
        "fraudLoss": stats.get("fraud_loss", 0),
        "legitimateVolume": stats.get("legit_volume", 0),
    }

    volume_data = list(
        collection.aggregate(
            [
                {
                    "$group": {
                        "_id": "$day",
                        "volume": {"$sum": "$transaction_amount"},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )
    )
    volume_by_day_data = [
        {"name": f"Day {item.get('_id')}", "volume": item.get("volume", 0)}
        for item in volume_data
        if item.get("_id") is not None
    ]

    channel_stats = list(
        collection.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "mobile": {"$sum": "$channel_mobile"},
                        "atm": {"$sum": "$channel_atm"},
                        "pos": {"$sum": "$channel_pos"},
                        "web": {"$sum": "$channel_web"},
                    }
                }
            ]
        )
    )
    channel_data = []
    if channel_stats:
        channels = channel_stats[0]
        channel_data = [
            {"name": "Mobile", "value": channels.get("mobile", 0), "color": "#3B82F6"},
            {"name": "ATM", "value": channels.get("atm", 0), "color": "#10B981"},
            {"name": "POS", "value": channels.get("pos", 0), "color": "#F59E0B"},
            {"name": "Web", "value": channels.get("web", 0), "color": "#EF4444"},
        ]

    hourly_data = list(
        collection.aggregate(
            [
                {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )
    )
    hourly = [
        {"name": f"{item.get('_id')}:00", "transactions": item.get("count", 0)}
        for item in hourly_data
        if item.get("_id") is not None
    ]

    daily_data = list(
        collection.aggregate(
            [
                {"$group": {"_id": "$weekday", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )
    )
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    daily: List[Dict[str, Any]] = []
    for item in daily_data:
        idx = item.get("_id")
        if isinstance(idx, int) and 0 <= idx < len(day_names):
            daily.append({"name": day_names[idx], "transactions": item.get("count", 0)})

    return {
        "analytics_metrics": analytics_metrics,
        "volume_by_day_data": volume_by_day_data,
        "channel_data": channel_data,
        "activity_data": {"hourly": hourly, "daily": daily},
    }


# ------------------------------------------------------------------
# NEW GEO ENDPOINTS FOR ACTIVITY MAP
# ------------------------------------------------------------------


@router.get("/geo/transactions")
async def geo_transactions(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),  # "minLon,minLat,maxLon,maxLat"
    limit: int = Query(500, gt=0, le=2000),
    min_risk: Optional[float] = Query(None),
    channel: Optional[str] = Query(None),
):
    """
    Return list of transactions with latitude & longitude (rounded).
    Query params:
      - start, end: ISO datetimes
      - bbox: minLon,minLat,maxLon,maxLat
      - limit: max records
      - min_risk: float filter
      - channel: filter
    """
    coll = get_collection("transactions")
    q: Dict[str, Any] = {}

    if start:
        try:
            q.setdefault("timestamp", {})["$gte"] = datetime.fromisoformat(start)
        except Exception:
            pass
    if end:
        try:
            q.setdefault("timestamp", {})["$lt"] = datetime.fromisoformat(end)
        except Exception:
            pass

    if min_risk is not None:
        q["risk_score"] = {"$gte": float(min_risk)}

    if channel:
        q["channel"] = channel

    if bbox:
        try:
            minLon, minLat, maxLon, maxLat = map(float, bbox.split(","))
            q["location"] = {
                "$geoWithin": {"$box": [[minLon, minLat], [maxLon, maxLat]]}
            }
        except Exception:
            pass

    cursor = coll.find(
        q,
        {
            "_id": 1,
            "transaction_id": 1,
            "amount": 1,
            "risk_score": 1,
            "channel": 1,
            "status": 1,
            "timestamp": 1,
            "location": 1,
            "customer_segment": 1,
        },
    ).sort("timestamp", -1).limit(limit)

    out: List[Dict[str, Any]] = []
    # NOTE: if you switch to Motor (async), change this to "async for"
    for doc in cursor:
        loc = doc.get("location")
        # Support [lon, lat] list or GeoJSON dict
        if isinstance(loc, list) and len(loc) >= 2:
            lon, lat = loc[0], loc[1]
        elif isinstance(loc, dict) and "coordinates" in loc:
            lon, lat = loc["coordinates"][0], loc["coordinates"][1]
        else:
            continue

        out.append(
            {
                "transaction_id": doc.get("transaction_id") or str(doc.get("_id")),
                "amount": doc.get("amount"),
                "risk_score": float(doc.get("risk_score") or 0.0),
                "channel": doc.get("channel"),
                "status": doc.get("status"),
                "timestamp": doc.get("timestamp").isoformat()
                if isinstance(doc.get("timestamp"), datetime)
                else doc.get("timestamp"),
                "lat": round(float(lat), 5),
                "lon": round(float(lon), 5),
                # avoid exposing PII: expose only segment or hashed id
                "customer_segment": doc.get("customer_segment", "unknown"),
            }
        )

    return {"count": len(out), "transactions": out}


@router.get("/geo/heatmap")
async def geo_heatmap(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    precision: int = Query(2, ge=1, le=5),
    min_risk: Optional[float] = Query(None),
    channel: Optional[str] = Query(None),
):
    """
    Return aggregated heatmap tiles by rounding lat/lon to precision decimals.
    precision=2 => coarse tiles, precision=4 => finer.
    """
    coll = get_collection("transactions")
    match: Dict[str, Any] = {}

    if start:
        try:
            match.setdefault("timestamp", {})["$gte"] = datetime.fromisoformat(start)
        except Exception:
            pass
    if end:
        try:
            match.setdefault("timestamp", {})["$lt"] = datetime.fromisoformat(end)
        except Exception:
            pass
    if min_risk is not None:
        match["risk_score"] = {"$gte": float(min_risk)}
    if channel:
        match["channel"] = channel

    pipeline: List[Dict[str, Any]] = [{"$match": match}] if match else []

    # Handle both:
    # - location: [lon, lat]
    # - location: { type: "Point", coordinates: [lon, lat] }
    pipeline += [
        {
            "$project": {
                "loc_array": {
                    "$cond": [
                        {"$isArray": "$location"},
                        "$location",
                        "$location.coordinates",
                    ]
                },
                "risk_score": 1,
            }
        },
        {"$match": {"loc_array": {"$ne": None}}},
        {
            "$addFields": {
                "lat_grid": {
                    "$round": [
                        {"$arrayElemAt": ["$loc_array", 1]},
                        precision,
                    ]
                },
                "lon_grid": {
                    "$round": [
                        {"$arrayElemAt": ["$loc_array", 0]},
                        precision,
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": {"lat": "$lat_grid", "lon": "$lon_grid"},
                "count": {"$sum": 1},
                "avg_risk": {"$avg": "$risk_score"},
                "lat": {"$first": "$lat_grid"},
                "lon": {"$first": "$lon_grid"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 1000},
    ]

    agg = list(coll.aggregate(pipeline))
    tiles: List[Dict[str, Any]] = []
    for t in agg:
        tiles.append(
            {
                "lat": round(float(t["lat"]), 5),
                "lon": round(float(t["lon"]), 5),
                "count": int(t["count"]),
                "avg_risk": float(t["avg_risk"] or 0.0),
            }
        )

    return {"tiles_count": len(tiles), "tiles": tiles}
