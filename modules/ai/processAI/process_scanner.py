import os
import joblib
import pandas as pd
import psutil
import hashlib

class ProcessThreatScanner:
    def __init__(self):
        self.model_dir = os.path.dirname(__file__)
        self.model_path = os.path.join(self.model_dir, "process_threat_model.pkl")
        self.features_path = os.path.join(self.model_dir, "process_threat_features.pkl")
        
        self.model = None
        self.features = None
        self.is_loaded = False
        
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path) and os.path.exists(self.features_path):
            try:
                import warnings
                warnings.filterwarnings("ignore", category=UserWarning)
                
                self.model = joblib.load(self.model_path)
                # CRITICAL: Prevent thread explosion on Windows during sequential inference
                if hasattr(self.model, 'n_jobs'):
                    self.model.n_jobs = 1
                    
                self.features = joblib.load(self.features_path)
                self.is_loaded = True
                print("[+] Process Threat Model loaded successfully.")
            except Exception as e:
                print(f"[-] Failed to load model: {e}")
        else:
            print("[-] Model files not found. Please train the model first.")

    def extract_features(self, proc: psutil.Process):
        """
        Extract real system telemetry features from the live process
        to feed into the Random Forest model.
        """
        cpu_percent = 0.0
        memory_percent = 0.0
        thread_count = 1
        is_system_user = 0
        is_temp_path = 0
        is_appdata_path = 0
        has_network = 0
        
        try:
            cpu_percent = proc.cpu_percent() or 0.0
        except: pass
        
        try:
            memory_percent = proc.memory_percent() or 0.0
        except: pass
        
        try:
            thread_count = proc.num_threads() or 1
        except: pass
        
        try:
            username = proc.username() or ''
            is_system_user = 1 if username.upper() in ['SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE'] else 0
        except: pass
        
        try:
            exe = proc.exe() or ''
            cmdline = " ".join(proc.cmdline() or [])
            full_path_context = (exe + " " + cmdline).lower()
            
            is_temp_path = 1 if 'temp' in full_path_context else 0
            is_appdata_path = 1 if 'appdata' in full_path_context else 0
        except: pass
        
        try:
            conns = proc.connections()
            has_network = 1 if conns and len(conns) > 0 else 0
        except: pass

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'thread_count': thread_count,
            'is_system_user': is_system_user,
            'is_temp_path': is_temp_path,
            'is_appdata_path': is_appdata_path,
            'has_network': has_network
        }

    def predict_threat_level(self, proc: psutil.Process) -> tuple:
        """
        Predicts threat level (1 to 5) and returns a color for UI mapping.
        Returns: (threat_level, color, probability)
        """
        if not self.is_loaded or self.model is None:
            return (1, "#00b894", 0.0) # Default safe if model not loaded

        try:
            # 1. Extract genuine telemetry features
            feature_dict = self.extract_features(proc)
            
            # 2. Convert to DataFrame
            df = pd.DataFrame([feature_dict])
            
            # 3. Predict threat score (0.0 to 1.0 continuous)
            prob = self.model.predict(df)[0]
            
            # 4. Map probability to threat levels (1 to 5)
            if prob <= 0.20:
                return (1, "#00b894", prob)  # Green / Safe
            elif prob <= 0.40:
                return (2, "#0984e3", prob)  # Blue / Low Risk
            elif prob <= 0.60:
                return (3, "#fdcb6e", prob)  # Yellow / Moderate Risk
            elif prob <= 0.80:
                return (4, "#e17055", prob)  # Orange / High Risk
            else:
                return (5, "#d63031", prob)  # Red / Critical
                
        except Exception as e:
            # If any error occurs (e.g., access denied to process info), default to safe/unknown
            return (1, "#636e72", 0.0) # Grey / Unknown
