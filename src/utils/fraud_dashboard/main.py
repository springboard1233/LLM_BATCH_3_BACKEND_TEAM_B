from fastapi import FastAPI
from routers import overview, insights, analytics, filters, alerts

app = FastAPI()

app.include_router(overview.router)
app.include_router(insights.router)
app.include_router(analytics.router)
app.include_router(filters.router)
app.include_router(alerts.router)
