from fastapi import FastAPI
from routers import overview, insights, analytics, filters, alerts
from fastapi.middleware.cors import CORSMiddleware
from analytics import router as analytics_router


app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router)
app.include_router(insights.router)
app.include_router(analytics.router)
app.include_router(filters.router)
app.include_router(alerts.router)
app.include_router(analytics_router)