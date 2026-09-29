import pandas as pd
import numpy as np
from datetime import timedelta

class FraudDetector:
    SPIKE_THRESHOLD = 4.0  # 4x user average
    VELOCITY_WINDOW_SECONDS = 60
    HIGH_RISK_SCORE = 80
    MEDIUM_RISK_SCORE = 50
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Ensure timestamp is datetime
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        # Use pre-calculated baseline from data generation (more accurate)
        # Fallback to median if not present
        if 'user_baseline' not in self.df.columns:
            self.df['user_baseline'] = self.df.groupby('user_id')['amount'].transform('median')
        
        # Keep original index for tracking
        self.df['original_index'] = self.df.index
    
    def detect_spikes(self, threshold_multiplier=None):
        """
        Detect spending spikes >4x user median (robust against outliers).
        Returns DataFrame with spike detection flag.
        """
        threshold = threshold_multiplier or self.SPIKE_THRESHOLD
        self.df['spike_detected'] = self.df['amount'] > (self.df['user_baseline'] * threshold)
        return self.df
    
    def detect_velocity(self, window_seconds=None):
        """
        Detect rapid velocity transactions within 60 seconds at different locations.
        """
        window = window_seconds or self.VELOCITY_WINDOW_SECONDS
        self.df['velocity_detected'] = False
        
        # For each user, find transactions within the velocity window at different locations
        for user_id in self.df['user_id'].unique():
            user_mask = self.df['user_id'] == user_id
            user_df = self.df[user_mask].sort_values('timestamp')
            indices = user_df.index.tolist()
            
            # Check all pairs within the time window
            for i, idx1 in enumerate(indices):
                for idx2 in indices[i+1:]:
                    time_diff = (user_df.loc[idx2, 'timestamp'] - user_df.loc[idx1, 'timestamp']).total_seconds()
                    
                    if time_diff <= window:
                        # Check if different locations
                        if user_df.loc[idx1, 'location'] != user_df.loc[idx2, 'location']:
                            self.df.loc[idx1, 'velocity_detected'] = True
                            self.df.loc[idx2, 'velocity_detected'] = True
                    else:
                        # Past window, can break early
                        break
        
        return self.df
    
    def assign_risk_scores(self):
        """
        Assign risk scores:
        - High: Both spike and velocity detected
        - Medium: Either spike or velocity detected (but not both)
        - Low: No anomalies
        """
        self.df['risk_score'] = 'Low'
        
        # Medium: spike XOR velocity
        medium_mask = (self.df['spike_detected'] != self.df['velocity_detected'])
        self.df.loc[medium_mask, 'risk_score'] = 'Medium'
        
        # High: both detected
        high_mask = self.df['spike_detected'] & self.df['velocity_detected']
        self.df.loc[high_mask, 'risk_score'] = 'High'
        
        # Numeric score
        self.df['risk_numeric'] = self.df['risk_score'].map({'Low': 25, 'Medium': 65, 'High': 95})
        
        return self.df
    
    def detect_all(self):
        """Run all detection methods."""
        self.detect_spikes()
        self.detect_velocity()
        self.assign_risk_scores()
        return self.df
    
    def get_flagged_transactions(self):
        """Return transactions with any detection."""
        flagged = self.df[
            (self.df['spike_detected'] == True) | 
            (self.df['velocity_detected'] == True)
        ].copy()
        return flagged
    
    def save_flagged(self, output_path):
        """Save flagged transactions to CSV."""
        flagged = self.get_flagged_transactions()
        flagged.to_csv(output_path, index=False)
        print(f"Flagged transactions saved to {output_path}")
        print(f"Total flagged: {len(flagged)}")
        print(f"  - High risk: {len(flagged[flagged['risk_score'] == 'High'])}")
        print(f"  - Medium risk: {len(flagged[flagged['risk_score'] == 'Medium'])}")
        print(f"  - Low risk: {len(flagged[flagged['risk_score'] == 'Low'])}")
        return flagged


if __name__ == "__main__":
    df = pd.read_csv("data/transactions.csv")
    detector = FraudDetector(df)
    detector.detect_all()
    flagged = detector.save_flagged("data/flagged_transactions.csv")
    print(f"\nDetection complete! {len(flagged)} transactions flagged.")