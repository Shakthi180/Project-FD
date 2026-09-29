import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detector import FraudDetector


class TestFraudDetector:
    """Test cases for FraudDetector."""

    @pytest.fixture
    def normal_transactions(self):
        """Create normal transactions with known values."""
        data = []
        for i in range(10):
            data.append({
                "transaction_id": f"TXN_{i:05d}",
                "user_id": "USER_0001",
                "amount": 100.0,
                "user_baseline": 100.0,
                "timestamp": datetime.now() - timedelta(hours=i),
                "location": "Singapore",
                "merchant_category": "Grocery"
            })
        return pd.DataFrame(data)

    @pytest.fixture
    def spike_transactions(self):
        """Create transactions with spending spikes >4x baseline."""
        data = []
        for i in range(5):
            # Normal transactions
            data.append({
                "transaction_id": f"TXN_{i:05d}",
                "user_id": "USER_0001",
                "amount": 100.0,
                "user_baseline": 100.0,
                "timestamp": datetime.now() - timedelta(hours=i+1),
                "location": "Singapore",
                "merchant_category": "Grocery"
            })
        # Spike transaction: 5x baseline
        data.append({
            "transaction_id": "TXN_99999",
            "user_id": "USER_0001",
            "amount": 500.0,  # 5x baseline
            "user_baseline": 100.0,
            "timestamp": datetime.now(),
            "location": "Singapore",
            "merchant_category": "Electronics"
        })
        return pd.DataFrame(data)

    @pytest.fixture
    def velocity_transactions(self):
        """Create transactions with rapid velocity (within 60s, different locations)."""
        base_time = datetime.now()
        data = [
            {
                "transaction_id": "TXN_00001",
                "user_id": "USER_0002",
                "amount": 200.0,
                "user_baseline": 100.0,
                "timestamp": base_time,
                "location": "Singapore",
                "merchant_category": "Grocery"
            },
            {
                "transaction_id": "TXN_00002",
                "user_id": "USER_0002",
                "amount": 150.0,
                "user_baseline": 100.0,
                "timestamp": base_time + timedelta(seconds=30),  # 30s later
                "location": "Malaysia",  # Different location
                "merchant_category": "Electronics"
            }
        ]
        return pd.DataFrame(data)

    def test_normal_transactions_low_risk(self, normal_transactions):
        """Normal transactions should be flagged as Low risk."""
        detector = FraudDetector(normal_transactions)
        detector.detect_all()
        
        assert all(detector.df['risk_score'] == 'Low'), "Normal transactions should be Low risk"
        assert not any(detector.df['spike_detected']), "No spikes should be detected"
        assert not any(detector.df['velocity_detected']), "No velocity should be detected"

    def test_spike_detection(self, spike_transactions):
        """Transactions >4x baseline should be flagged as spikes."""
        detector = FraudDetector(spike_transactions)
        detector.detect_all()
        
        # Find the spike transaction
        spike_rows = detector.df[detector.df['spike_detected'] == True]
        assert len(spike_rows) > 0, "Spike transaction should be detected"
        
        # Verify it's the high amount transaction
        assert (detector.df.loc[detector.df['amount'] == 500.0, 'spike_detected'].values[0] == True), \
            "500.0 amount (5x baseline) should trigger spike detection"

    def test_velocity_detection(self, velocity_transactions):
        """Transactions within 60s at different locations should be flagged as velocity."""
        detector = FraudDetector(velocity_transactions)
        detector.detect_all()
        
        # Both transactions should be velocity flagged
        assert all(detector.df['velocity_detected'] == True), \
            "Both velocity transactions should be detected"

    def test_risk_scoring_high(self, spike_transactions):
        """Transactions with both spike and velocity should be High risk."""
        # Add a velocity component to spike transaction
        spike_transactions.loc[spike_transactions['transaction_id'] == 'TXN_99999', 'timestamp'] = datetime.now()
        spike_transactions.loc[spike_transactions.index[0], 'timestamp'] = datetime.now() - timedelta(seconds=30)
        spike_transactions.loc[spike_transactions.index[0], 'location'] = 'Different Location'
        
        detector = FraudDetector(spike_transactions)
        detector.detect_all()
        
        # Check for High risk
        high_risk = detector.df[detector.df['risk_score'] == 'High']
        assert len(high_risk) > 0, "Should have High risk transactions when both spike and velocity detected"

    def test_risk_scoring_medium(self, spike_transactions):
        """Transactions with only spike or only velocity should be Medium risk."""
        detector = FraudDetector(spike_transactions)
        detector.detect_all()
        
        # Spike-only transactions should be Medium
        medium_risk = detector.df[detector.df['risk_score'] == 'Medium']
        assert len(medium_risk) > 0, "Should have Medium risk transactions"

    def test_get_flagged_transactions(self, spike_transactions):
        """get_flagged_transactions should return only flagged rows."""
        detector = FraudDetector(spike_transactions)
        detector.detect_all()
        
        flagged = detector.get_flagged_transactions()
        assert len(flagged) > 0, "Should return flagged transactions"
        
        # All flagged should have either spike or velocity
        assert all(flagged['spike_detected'] | flagged['velocity_detected'])

    def test_baseline_fallback(self, normal_transactions):
        """If user_baseline not in data, should calculate from median."""
        # Remove user_baseline column
        test_df = normal_transactions.drop(columns=['user_baseline'])
        
        detector = FraudDetector(test_df)
        detector.detect_all()
        
        # Should still work without error
        assert 'user_baseline' in detector.df.columns, "Should calculate baseline as fallback"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])