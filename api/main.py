from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import os

app = FastAPI(title="Financial Fraud & Anomaly Detector API")

# In-memory user spending baselines (loaded from data for realistic detection)
USER_BASELINES = {}


def load_user_baselines():
    """Load user spending baselines from transactions data."""
    try:
        df = pd.read_csv("data/transactions.csv")
        # Use median for robust baseline calculation
        baselines = df.groupby('user_id')['amount'].median().to_dict()
        return baselines
    except Exception:
        # Fallback defaults if data not available
        return {
            "USER_0001": 100.0,
            "USER_0002": 150.0,
            "USER_0003": 80.0,
        }


# Load baselines on startup
USER_BASELINES = load_user_baselines()


class TransactionPayload(BaseModel):
    """Pydantic model for incoming transaction data."""
    user_id: str
    amount: float
    timestamp: str
    location: str
    merchant_category: str


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Fraud Detector API"}


@app.post("/api/v1/detect")
def detect_fraud(payload: TransactionPayload):
    """
    Detect fraud for a single transaction.
    
    Rules:
    - Spike: amount > 3.5x user baseline
    - Velocity: high amount transactions in high-risk categories
    - Location risk: certain merchant categories with high amounts
    """
    reasons = []
    risk_score = "Low"
    flagged = False
    
    # Get user baseline (default if not found)
    user_baseline = USER_BASELINES.get(payload.user_id, 100.0)
    
    # Spike detection: amount > 3.5x user average
    spike_threshold = 3.5
    if payload.amount > user_baseline * spike_threshold:
        reasons.append(f"Spike > {spike_threshold}x average (${payload.amount:.2f} vs ${user_baseline:.2f} baseline)")
        flagged = True
    
    # High-risk merchant categories
    high_risk_categories = ['Electronics', 'Jewelry', 'Travel', 'Luxury']
    if payload.merchant_category in high_risk_categories and payload.amount > 500:
        reasons.append(f"High-value purchase in high-risk category: {payload.merchant_category}")
        flagged = True
    
    # Very high amount detection
    if payload.amount > 1000:
        reasons.append(f"Very high transaction amount: ${payload.amount:.2f}")
        flagged = True
    
    # Determine risk score
    if flagged:
        if len(reasons) >= 2 or payload.amount > user_baseline * 5:
            risk_score = "High"
        else:
            risk_score = "Medium"
    
    # Generate transaction ID
    timestamp_hash = int(datetime.now().timestamp() * 1000) % 1000000
    transaction_id = f"TXN_LIVE_{timestamp_hash}"
    
    return {
        "transaction_id": transaction_id,
        "user_id": payload.user_id,
        "risk_score": risk_score,
        "flagged": flagged,
        "reasons": reasons,
        "amount": payload.amount,
        "user_baseline": user_baseline
    }


@app.get("/api/v1/users")
def get_users():
    """Get list of users and their baselines."""
    return {"users": list(USER_BASELINES.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)