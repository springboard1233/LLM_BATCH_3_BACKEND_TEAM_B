

import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.fraud_dashboard.cache import get_redis_client
from src.utils.fraud_dashboard.routers import analytics, overview, alerts, insights, filters
from src.utils.fraud_dashboard.routers import prediction
from src.utils.fraud_dashboard.routers import feedback
from src.utils.fraud_dashboard.routers import auth


app = FastAPI()


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    app.redis_client = get_redis_client()
   

app.include_router(analytics.router, prefix="/api")
app.include_router(overview.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
app.include_router(filters.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(prediction.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# app.include_router(analytics_router)
@app.get("/")
async def root():
    return {"message": "Welcome to the Fraud Analytics API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
