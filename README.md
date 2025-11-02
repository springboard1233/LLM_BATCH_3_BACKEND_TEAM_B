# 🚀 Fraud Analytics API (FastAPI + MongoDB + Caching)

This project is a Fraud Analytics backend service built using **FastAPI**, **MongoDB**, and **in-memory caching**.  
It exposes APIs to analyze transaction data, detect fraud trends, show suspicious activity, and support dashboard visualization.

---

## 📁 Project Structure


---

## ✅ Key Features

### ✅ 1. Data Overview (Mandatory)
- Total records
- Fraud vs. Non-fraud counts
- Fraud distribution charts

### ✅ 2. Key Insights
- Average / max / min transaction amount
- Fraud detection rate

### ✅ 3. Visual Analytics
- Fraud trend by date/month
- Channel/device fraud ratio
- Correlation heatmap (optional)

### ✅ 4. Data Filters
Filter using:
- Time range
- Channel / Transaction type
- Customer segments

### ✅ 5. Alerts Section
Shows:
- Top suspicious transactions
- Anomalies by amount/timing

### 🎁 Bonus (Later)
- Export CSV/Excel
- ML model performance metrics
- Real-time refresh indicator

---

## 🧰 Requirements

Make sure you have:

- Python **3.9+**
- MongoDB Atlas access

---




## 🏁 Project Entry Point – `main.py`

Overview

This file initializes the FastAPI backend application for the Fraud Analytics Dashboard.
It configures CORS, mounts all route modules, and serves as the single startup point for the backend service.

Responsibilities

Initializes the FastAPI app.

Configures CORS for frontend–backend communication.

Includes routers for all analytics modules:

  overview
  
  insights
  
  analytics
  
  filters
  
  alerts

Runs the analytics API on the configured host/port.

CORS Configuration

The middleware allows requests from both React (Vite) and Next.js local development environments:

origins = [
    "http://localhost:5173",    
    # React + Vite default
    "http://127.0.0.1:5173",
    "http://localhost:3000",      # Next.js / React default
    "http://127.0.0.1:3000",
    "*"                           # Allow all (for testing only)
]


🟨 Note:
In production, replace "*" with your deployed frontend URL for better security.

Router Registration

Each analytics feature is modularized into its own router under the routers/ directory:

Router Module	Purpose
overview.py	Returns dataset summary (record count, fraud vs non-fraud ratio, etc.)
insights.py	Provides key metrics like average transaction amount and detection rate
analytics.py	Handles visual charts — volume, channel breakdown, activity heatmaps
filters.py	Adds time-based or customer-segment filters
alerts.py	Lists top suspicious or high-risk transactions

Finally, all routers are included using:

app.include_router(overview.router)
app.include_router(insights.router)
app.include_router(analytics.router)
app.include_router(filters.router)
app.include_router(alerts.router)
app.include_router(analytics_router)  # additional route inclusion

How to Run the Backend

Run the FastAPI app locally using Uvicorn:

uvicorn main:app --reload


Your backend will be available at:

http://127.0.0.1:8000



## 🟦 1. Overview Routes (`/overview`)

These endpoints provide top-level statistics and summary metrics for the dashboard home screen.  
Useful for KPI cards, at-a-glance fraud understanding, and trend widgets.

---

### 📌 `GET /overview/stats`

Fetches high-level transaction and fraud summary metrics.

#### ✅ Sample Response
```json
{
  "total_transactions": 150000,
  "total_fraud": 5230,
  "fraud_percentage": 3.48,
  "active_users": 92000,
  "average_transaction_amount": 245.87,
  "high_risk_transactions": 1420
}
```

| Key                          | Meaning                                     | Usage in Frontend   |
| ---------------------------- | ------------------------------------------- | ------------------- |
| `total_transactions`         | Count of all transactions stored in DB      | KPI card            |
| `total_fraud`                | Number of confirmed fraudulent transactions | Fraud bar/badge     |
| `fraud_percentage`           | Ratio: fraud ÷ total × 100                  | Trend comparison    |
| `active_users`               | Estimated users triggering transactions     | User timeline chart |
| `average_transaction_amount` | Mean amount of all transactions             | Pie chart reference |
| `high_risk_transactions`     | Transactions matching risk rules            | Alerts widget       |



🧪 Test via Swagger UI

Open:
```
http://127.0.0.1:8000/docs
```

| Status       | Cause                    |
| ------------ | ------------------------ |
| 500          | DB connection issue      |
| empty values | No records in collection |



Endpoint

GET /insights/transaction-amounts

📝 Description

Returns aggregated transactional analytics:

Volume distribution by time interval

Breakdown by channel (ATM, Mobile, POS, Web)

Fraud loss estimate

Legitimate transaction volume

Hourly distribution of transactions

Daily activity heatmaps

This is the most chart-heavy dataset in the dashboard.

📥 Sample Response

```
{
  "volume_data": [
    { "_id": 1, "count": 168 },
    { "_id": 2, "count": 214 },
    ...
    { "_id": 25, "count": 204 }
  ],
  "channel_distribution": [
    {
      "_id": null,
      "atm": 490,
      "mobile": 1992,
      "pos": 784,
      "web": 1734
    }
  ],
  "fraud_loss": 129.64832588836464,
  "legit_volume": 537.5441538207425,
  "hourly_distribution": [
    { "_id": 0, "count": 203 },
    ...
    { "_id": 23, "count": 220 }
  ],
  "daily_activity": []
}

```
Key Explanation of JSON Fields
| Field                   | Meaning                                                   | Usage in Dashboard            |
| ----------------------- | --------------------------------------------------------- | ----------------------------- |
| `volume_data`           | Transaction count segmented by buckets (frequency groups) | Bar chart showing volume load |
| `_id`                   | Group identifier (ex: bucket index)                       | X-axis labels                 |
| `count`                 | Number of transactions in each bucket                     | Y-axis frequency              |
| `channel_distribution`  | Aggregated by transaction channel                         | Donut chart / Pie chart       |
| `atm, mobile, pos, web` | Channel-wise transaction volume                           | Category comparison           |
| `fraud_loss`            | Total value lost due to fraud (estimated)                 | KPI card / metric tile        |
| `legit_volume`          | Total legitimate transaction value                        | KPI cards                     |
| `hourly_distribution`   | Number of transactions per hour (0–23)                    | Line chart                    |
| `daily_activity`        | Placeholder for day-based heatmap                         | Future heatmap scope          |






3. Analytics Core API

The Analytics Router provides the core statistical signals used for fraud monitoring and dashboard KPIs.
These values are derived from MongoDB aggregation pipelines and serve as the main cards and trend charts in the UI.

✅ Endpoint

GET /analytics/summary

📝 Description

Returns aggregated metrics related to:

Total transaction count

Total fraud count

Fraud ratio (percentage)

Total financial loss due to fraud

Comparison between legitimate vs fraudulent behavior

Channel usage trends

This endpoint powers the summary KPI cards and overview analytics.

📥 Sample Response (example shape)
```
{
  "total_transactions": 5000,
  "fraudulent_transactions": 412,
  "legitimate_transactions": 4588,
  "fraud_rate_percentage": 8.24,
  "total_loss_amount": 129.64,
  "average_transaction_amount": 0.58,
  "channel_usage": {
    "atm": 490,
    "mobile": 1992,
    "pos": 784,
    "web": 1734
  }
}

```
| Field                        | Meaning                                     |
| ---------------------------- | ------------------------------------------- |
| `total_transactions`         | How many transactions exist in the database |
| `fraudulent_transactions`    | Count where `is_fraud = 1`                  |
| `legitimate_transactions`    | Count where `is_fraud = 0`                  |
| `fraud_rate_percentage`      | (fraudulent / total) * 100                  |
| `total_loss_amount`          | Sum of all fraud transaction amounts        |
| `average_transaction_amount` | Mean amount across all events               |
| `channel_usage`              | Channel-wise traffic distribution           |

UI LEVEL USAGE:

| Dashboard Section          | Data Origin                               |
| -------------------------- | ----------------------------------------- |
| KPI Summary Cards          | total_transactions, fraud_rate_percentage |
| Loss Indicator Tile        | total_loss_amount                         |
| Traffic Distribution Donut | channel_usage                             |
| Fraud Trend                | fraudulent_transactions count             |


4. Filters API

The Filter Router allows the frontend to dynamically fetch transactions based on user-selected filters such as:

Date range

Transaction channel

(future) Amount range, fraud flag, hour window, etc.

This is used in:
✅ Transaction table
✅ Analytics deep-dives
✅ Drill-down analysis

✅ Endpoint

GET /filter/transactions

📌 Query Parameters Supported
| Parameter    | Type                | Example      | Purpose                                 |
| ------------ | ------------------- | ------------ | --------------------------------------- |
| `start_date` | string (ISO format) | `2025-08-10` | Lower bound for filtering               |
| `end_date`   | string (ISO format) | `2025-08-20` | Upper bound for filtering               |
| `channel`    | string              | `"atm"`      | Filters by transaction channel set to 1 |



🧾 Response shape

Each document returned:
```
{
  "timestamp": "2025-08-10T14:32:11",
  "transaction_amount": 0.42,
  "atm": 1,
  "mobile": 0,
  "pos": 0,
  "web": 0,
  "is_fraud": 0
}

```

5. Analytics APIs

These endpoints power the core dashboard visualizations:

Trend charts

Fraud comparison

Channel-wise breakdowns

Heatmaps

Activity timelines

These are consumed by front-end chart components (Recharts, Chart.js, ApexCharts, etc.)





✅ Endpoint

GET /analytics/fraud_trend

📌 What it does

Aggregates all transactions by day, grouping:

fraud counts

total daily volume

This powers a line chart / bar trend showing how fraud fluctuates over time.

🧠 Pipeline logic

Group by year/month/day

Count fraud

Count total

Sort descending

Response example
```
[
  {
    "_id": {
      "year": 2025,
      "month": 8,
      "day": 25
    },
    "fraud_count": 15,
    "total": 204
  },
  {
    "_id": {
      "year": 2025,
      "month": 8,
      "day": 10
    },
    "fraud_count": 17,
    "total": 184
  }
]

```

How to interpret


| Field                | Meaning                                    |
| -------------------- | ------------------------------------------ |
| `_id.year/month/day` | Date bucket                                |
| `fraud_count`        | Total fraudulent transactions on that date |
| `total`              | Total transactions on that date            |




7. Dashboard Analytics (Main Composite Endpoint)

This is the most important endpoint powering the primary dashboard cards, charts, and graphs.

✅ Endpoint

GET /analytics/dashboard

📌 What it does

Returns multiple aggregated analytics in one response:

Daily transaction volume

Channel distribution

Estimated fraud loss

Legit transaction volume

Hourly activity distribution

Daily activity breakdown

This reduces frontend network calls (performance optimized).

✅ Response Example (trimmed for clarity)
```
{
  "volume_data": [
    { "_id": 1, "count": 168 },
    { "_id": 2, "count": 214 },
    ...
  ],

  "channel_distribution": [
    {
      "_id": null,
      "atm": 490,
      "mobile": 1992,
      "pos": 784,
      "web": 1734
    }
  ],

  "fraud_loss": 129.64832588836464,

  "legit_volume": 537.5441538207425,

  "hourly_distribution": [
    { "_id": 0, "count": 203 },
    { "_id": 1, "count": 192 },
    ...
  ],

  "daily_activity": [
    { "_id": 1, "count": 168 },
    ...
  ]
}

```
🧠 Breakdown of Each Field
1️⃣ volume_data

Represents transaction counts grouped by day.

Use case:

Daily activity line chart

Transaction heatmap

Volume patterns


| Field  | Meaning            |
| ------ | ------------------ |
| atm    | ATM withdrawals    |
| mobile | UPI/Mobile banking |
| pos    | Card swipes        |
| web    | Online payments    |




Use case:

Donut/Pie chart distribution

Channel risk highlight

3️⃣ fraud_loss

Estimated monetary loss due to fraudulent activity.

UI:

Red metric card

Alert banner

Trend gauge

4️⃣ legit_volume

Total sum of legitimate transaction amounts.

UI:

Green metric card

Growth indicator

5️⃣ hourly_distribution

Transaction activity grouped by hour (0–23).

Use case:

Behavior heatmap

Rush-hour detection


6️⃣ daily_activity

Mirrors volume_data but can be used separately.

Use case:

Additional insights

Comparison charts

Multi-week trends
