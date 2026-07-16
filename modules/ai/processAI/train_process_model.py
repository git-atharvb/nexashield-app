import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib

def generate_synthetic_dataset(samples=10000):
    np.random.seed(42)
    
    # Feature ranges
    # cpu_percent: 0 to 100
    # memory_percent: 0 to 100
    # thread_count: 1 to 200
    # is_system_user: 0 or 1
    # is_temp_path: 0 or 1
    # is_appdata_path: 0 or 1
    # has_network: 0 or 1
    
    data = []
    labels = []
    
    for _ in range(samples):
        # Base realistic distributions
        cpu = max(0, np.random.normal(5, 10))
        mem = max(0.1, np.random.normal(2, 5))
        threads = int(max(1, np.random.normal(15, 10)))
        sys_user = np.random.choice([0, 1], p=[0.7, 0.3])
        temp_path = np.random.choice([0, 1], p=[0.95, 0.05])
        appdata_path = np.random.choice([0, 1], p=[0.9, 0.1])
        network = np.random.choice([0, 1], p=[0.8, 0.2])
        
        # Threat logic injection to create clear patterns for the ML model
        threat = 0 # default benign
        
        # Continuous threat logic to hit all 5 colors
        threat = 0.1 # default safe
        
        # We define a continuous threat score (0.0 to 1.0)
        score = 0.1
        
        # Base penalties
        if temp_path:
            score += 0.4
        if appdata_path:
            score += 0.2
        if network:
            score += 0.2
            
        # CPU scaling (up to +0.3 for 100% CPU)
        score += (cpu / 100.0) * 0.3
        
        # Thread scaling (up to +0.1 for high threads)
        score += min(0.1, (threads / 200.0) * 0.1)
        
        # Special overrides for the simulator to guarantee colors based on specific CLI flags
        if np.random.random() < 0.05:
            # Noise
            score += np.random.normal(0, 0.05)
            
        score = max(0.0, min(1.0, score))
            
        # Bound limits
        cpu = min(100.0, cpu)
        mem = min(100.0, mem)
            
        data.append([cpu, mem, threads, sys_user, temp_path, appdata_path, network])
        labels.append(score)
        
    df = pd.DataFrame(data, columns=['cpu_percent', 'memory_percent', 'thread_count', 'is_system_user', 'is_temp_path', 'is_appdata_path', 'has_network'])
    df['threat_score'] = labels
    return df

def train_model():
    print("[*] Generating synthetic system telemetry dataset...")
    df = generate_synthetic_dataset(15000)

    X = df.drop(columns=['threat_score'])
    y = df['threat_score']

    print("[*] Splitting dataset into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("[*] Training Random Forest Regressor on system telemetry...")
    clf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    clf.fit(X_train, y_train)

    print("[*] Evaluating model...")
    y_pred = clf.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"[+] Model Mean Squared Error: {mse:.4f}")

    model_dir = os.path.dirname(__file__)
    model_path = os.path.join(model_dir, "process_threat_model.pkl")
    print(f"[*] Saving telemetry model to {model_path}...")
    joblib.dump(clf, model_path)
    
    features_path = os.path.join(model_dir, "process_threat_features.pkl")
    joblib.dump(list(X.columns), features_path)
    print("[+] Training complete!")

if __name__ == "__main__":
    train_model()
