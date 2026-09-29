# Automated Financial Fraud & Anomaly Detector

## Overview

A real-time financial fraud detection system that identifies suspicious transactions using dual statistical engines:

1. **Spike Detection** - Flags transactions exceeding 3.5x the user's average spending
2. **Velocity Detection** - Identifies rapid transactions within 60 seconds across different locations

The system processes transaction data through a pipeline that generates synthetic data, runs statistical detection, exposes a REST API, and visualizes results in an interactive dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRAUD DETECTION SYSTEM                       │
└─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
   │   Data Engine   │────▶│ Detection Engine │────▶│  FastAPI REST   │
   │  (generate_data)│     │    (detector)    │     │      API        │
   └────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
            │                       │                        │
            ▼                       ▼                        ▼
   ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
   │ transactions.csv│     │ flagged_trans   │     │   /health       │
   │ (1000 records   │     │ actions.csv     │     │   /api/v1/detect│
   │  50 anomalies)  │     │ (risk scores)   │     │   /api/v1/users │
   └─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                              │
                                              ┌───────────────┘
                                              ▼
                                    ┌─────────────────────┐
                                    │    Streamlit        │
                                    │    Dashboard        │
                                    │  - KPIs             │
                                    │  - Charts (Plotly)  │
                                    │  - Interactive Table│
                                    └─────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13 |
| Data Processing | Pandas, NumPy |
| Data Generation | Faker |
| API Framework | FastAPI, Uvicorn |
| Validation | Pydantic |
| Dashboard | Streamlit, Plotly |
| Testing | Pytest |
| Virtual Environment | venv |

## Setup & Installation

### 1. Clone and Navigate

```bash
cd Project-FD
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install pandas faker pytest fastapi uvicorn streamlit plotly pydantic
```

### 5. Generate Test Data

```bash
python data/generate_data.py
```

### 6. Run Detection Engine

```bash
python engine/detector.py
```

### 7. Run Unit Tests

```bash
pytest engine/test_detector.py -v
```

Expected output:
```
============================= test session starts =============================
...
engine/test_detector.py::TestFraudDetector::test_normal_transactions_low_risk PASSED
engine/test_detector.py::TestFraudDetector::test_spike_detection PASSED
engine/test_detector.py::TestFraudDetector::test_velocity_detection PASSED
...
============================== 7 passed in 0.79s ==============================
```

## How to Run

### FastAPI Server (REST API)

```bash
uvicorn api.main:app --reload --port 8000
```

The API will be available at:
- **Base URL**: http://127.0.0.1:8000
- **Swagger Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Streamlit Dashboard (Visualization)

```bash
streamlit run dashboard/app.py
```

The dashboard will open at: http://localhost:8503

## API Reference

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "Fraud Detector API"
}
```

### Detect Fraud

```bash
curl -X POST http://127.0.0.1:8000/api/v1/detect \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_0001",
    "amount": 500.0,
    "timestamp": "2024-01-15T10:30:00",
    "location": "Singapore",
    "merchant_category": "Electronics"
  }'
```

**Response:**
```json
{
  "transaction_id": "TXN_LIVE_514729",
  "user_id": "USER_0001",
  "risk_score": "Medium",
  "flagged": true,
  "reasons": [
    "Spike > 3.5x average ($500.00 vs $128.61 baseline)"
  ],
  "amount": 500.0,
  "user_baseline": 128.61
}
```

### High-Risk Example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/detect \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_0002",
    "amount": 1500.0,
    "timestamp": "2024-01-15T10:30:00",
    "location": "Malaysia",
    "merchant_category": "Jewelry"
  }'
```

**Response:**
```json
{
  "transaction_id": "TXN_LIVE_514731",
  "user_id": "USER_0002",
  "risk_score": "High",
  "flagged": true,
  "reasons": [
    "Spike > 3.5x average ($1500.00 vs $67.18 baseline)",
    "High-value purchase in high-risk category: Jewelry",
    "Very high transaction amount: $1500.00"
  ],
  "amount": 1500.0,
  "user_baseline": 67.18
}
```

## Project Structure

```
Project-FD/
├── api/
│   └── main.py              # FastAPI REST API
├── dashboard/
│   └── app.py               # Streamlit dashboard
├── data/
│   ├── generate_data.py     # Synthetic data generator
│   ├── transactions.csv     # Generated transaction data
│   └── flagged_transactions.csv  # Detection results
├── engine/
│   ├── detector.py          # Fraud detection engine
│   └── test_detector.py     # Unit tests
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Detection Rules

| Rule | Condition | Risk Level |
|------|-----------|------------|
| Spike | Amount > 3.5x user baseline | Medium |
| Velocity | Multiple transactions <60s at different locations | Medium |
| High-Risk Category | Electronics/Jewelry/Travel/Luxury >$500 | Medium |
| Very High Amount | Transaction > $1000 | High |
| Combined | Multiple rules triggered | High |

## Risk Scoring

- **Low**: No anomalies detected
- **Medium**: Single rule triggered (spike OR velocity)
- **High**: Multiple rules triggered OR very high amounts

## License

This project is for demonstration purposes.