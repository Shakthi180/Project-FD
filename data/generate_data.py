import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

def generate_transactions(num_records=1000):
    users = [f"USER_{i:04d}" for i in range(1, 51)]
    categories = ['Grocery', 'Electronics', 'Entertainment', 'Travel', 'Utilities']
    locations = [fake.city() for _ in range(20)]
    
    start_time = datetime.now() - timedelta(days=30)
    
    # STEP 1: Generate baseline normal transactions to calculate user averages
    user_normal_amounts = {u: [] for u in users}
    
    # Generate normal transactions only
    for i in range(num_records):
        user = random.choice(users)
        amount = round(random.uniform(5.0, 200.0), 2)
        user_normal_amounts[user].append(amount)
    
    # Calculate user baselines (using median for robustness)
    user_baselines = {}
    for u in users:
        if user_normal_amounts[u]:
            user_baselines[u] = np.median(user_normal_amounts[u])
        else:
            user_baselines[u] = 50.0
    
    # STEP 2: Identify 50 anomaly indices
    anomaly_count = 50
    normal_indices = list(range(num_records))
    anomaly_indices = set(random.sample(normal_indices, anomaly_count))
    
    # Separate spike and velocity indices
    spike_indices = set(random.sample(list(anomaly_indices), 25))
    velocity_indices = anomaly_indices - spike_indices  # Remaining 25
    
    # STEP 3: Generate all transactions
    data = []
    for i in range(num_records):
        user = random.choice(users)
        user_baseline = user_baselines[user]
        
        if i in spike_indices:
            # Spending spike >4x user baseline
            amount = round(random.uniform(user_baseline * 4.5, user_baseline * 8.0), 2)
        elif i in velocity_indices:
            # Velocity transaction (will be paired)
            amount = round(random.uniform(50.0, 500.0), 2)
        else:
            # Normal transaction
            amount = round(random.uniform(5.0, 200.0), 2)
        
        data.append({
            "transaction_id": f"TXN_{i:06d}",
            "user_id": user,
            "amount": amount,
            "user_baseline": user_baselines[user],  # Pre-calculated baseline
            "timestamp": start_time + timedelta(minutes=random.randint(1, 43200)),
            "location": random.choice(locations),
            "merchant_category": random.choice(categories),
            "is_anomaly": i in anomaly_indices,
            "anomaly_type": 'spike' if i in spike_indices else ('velocity' if i in velocity_indices else 'normal')
        })
    
    # STEP 4: Create velocity pairs (transactions within 60s at different locations)
    velocity_list = list(velocity_indices)
    random.shuffle(velocity_list)
    
    for i in range(0, len(velocity_list) - 1, 2):
        t1_idx = velocity_list[i]
        t2_idx = velocity_list[i + 1]
        
        base_time = data[t1_idx]['timestamp']
        # Both transactions within 60 seconds
        data[t1_idx]['timestamp'] = base_time
        data[t2_idx]['timestamp'] = base_time + timedelta(seconds=random.randint(10, 60))
        
        # Different locations
        loc1 = random.choice(locations)
        data[t1_idx]['location'] = loc1
        data[t2_idx]['location'] = random.choice([l for l in locations if l != loc1])
    
    # Create DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv("data/transactions.csv", index=False)
    
    print(f"Dataset created at data/transactions.csv")
    print(f"Total records: {len(df)}")
    print(f"Spike anomalies: {len([x for x in df['anomaly_type'] if x == 'spike'])}")
    print(f"Velocity anomalies: {len([x for x in df['anomaly_type'] if x == 'velocity'])}")
    
    return df


if __name__ == "__main__":
    generate_transactions()