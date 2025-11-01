from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.fraud_dashboard.router import fraud_dashboard_router
from src.utils.fraud_dashboard.database import init_db

app = FastAPI(
    title="Fraud Detection Dashboard API",
    description="API for fraud detection dashboard with database integration",
    version="1.0.0"
)

# More secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (alternative port)
        "http://localhost:3001",  # Alternative React port
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
    ],
)

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(fraud_dashboard_router, prefix="/")