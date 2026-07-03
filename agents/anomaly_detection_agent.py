# agents/anomaly_detection_agent.py
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from loguru import logger

# Use relative import
from .base_agent import BaseAgent

class AnomalyDetectionAgent(BaseAgent):
    """Agent responsible for detecting anomalies in vehicle sensor data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("anomaly_detection_agent", config)
        self.models = {}
        self.data_history = {}
        self.anomaly_threshold = config.get("anomaly_threshold", -0.1)
        self.training_size = config.get("training_size", 50)
        self.retrain_frequency = config.get("retrain_frequency", 20)
        self.scalers = {}
        self.sensors = [
            "engine_temp", "oil_pressure", "rpm", "speed",
            "fuel_level", "battery_voltage", "coolant_temp",
            "transmission_temp", "brake_pad_wear", "tire_pressure"
        ]
        logger.info(f"AnomalyDetectionAgent initialized with threshold={self.anomaly_threshold}")
        
    async def train_model(self, vehicle_id: str) -> None:
        """Train Isolation Forest model for a vehicle"""
        if vehicle_id not in self.data_history or len(self.data_history[vehicle_id]) < 10:
            logger.debug(f"Not enough data to train model for {vehicle_id}")
            return
        
        try:
            df = pd.DataFrame(self.data_history[vehicle_id])
            feature_columns = [col for col in df.columns if col in self.sensors]
            
            if len(feature_columns) > 0:
                X = df[feature_columns].values
                X = np.nan_to_num(X, nan=0.0)
                
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                self.scalers[vehicle_id] = scaler
                
                model = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_estimators=100
                )
                model.fit(X_scaled)
                self.models[vehicle_id] = model
                
                logger.info(f"Model trained for vehicle {vehicle_id} with {len(X)} samples")
                
        except Exception as e:
            logger.error(f"Error training model for {vehicle_id}: {str(e)}")
    
    async def detect_anomalies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in sensor data"""
        vehicle_id = data.get("vehicle_id")
        
        if not vehicle_id:
            logger.error("No vehicle_id in data")
            return data
        
        if vehicle_id not in self.data_history:
            self.data_history[vehicle_id] = []
        
        self.data_history[vehicle_id].append(data)
        
        if len(self.data_history[vehicle_id]) > 1000:
            self.data_history[vehicle_id] = self.data_history[vehicle_id][-1000:]
        
        if (vehicle_id not in self.models or 
            len(self.data_history[vehicle_id]) % self.retrain_frequency == 0):
            await self.train_model(vehicle_id)
        
        anomaly_detected = False
        anomaly_scores = {}
        anomaly_details = []
        
        if vehicle_id in self.models:
            try:
                features = []
                valid_sensors = []
                
                for sensor in self.sensors:
                    if sensor in data and data[sensor] is not None:
                        features.append(data[sensor])
                        valid_sensors.append(sensor)
                    else:
                        features.append(0)
                
                if features:
                    X = np.array(features).reshape(1, -1)
                    
                    if vehicle_id in self.scalers:
                        X_scaled = self.scalers[vehicle_id].transform(X)
                    else:
                        X_scaled = X
                    
                    score = self.models[vehicle_id].decision_function(X_scaled)[0]
                    
                    for i, sensor in enumerate(valid_sensors):
                        if sensor in data and data[sensor] is not None:
                            historical_values = []
                            for d in self.data_history[vehicle_id][-20:]:
                                if sensor in d and d[sensor] is not None:
                                    historical_values.append(d[sensor])
                            
                            if len(historical_values) > 0:
                                mean_val = np.mean(historical_values)
                                std_val = np.std(historical_values)
                                
                                if std_val > 0:
                                    z_score = abs(data[sensor] - mean_val) / std_val
                                    if z_score > 3:
                                        anomaly_details.append({
                                            "sensor": sensor,
                                            "value": data[sensor],
                                            "mean": mean_val,
                                            "z_score": z_score,
                                            "threshold_exceeded": True
                                        })
                    
                    anomaly_scores = {
                        "overall_score": score,
                        "is_anomaly": score < self.anomaly_threshold or len(anomaly_details) > 0,
                        "details": anomaly_details
                    }
                    
                    anomaly_detected = score < self.anomaly_threshold or len(anomaly_details) > 0
                    
                    if anomaly_detected:
                        logger.warning(f"Anomaly detected for vehicle {vehicle_id}: score={score:.3f}")
                        
            except Exception as e:
                logger.error(f"Error in anomaly detection: {str(e)}")
        
        result = {
            **data,
            "anomaly_detected": anomaly_detected,
            "anomaly_scores": anomaly_scores,
            "detection_timestamp": datetime.now().isoformat()
        }
        
        if anomaly_detected:
            await self.send_message(
                "diagnosis_agent",
                "anomaly_detected",
                result
            )
        
        return result
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data and detect anomalies"""
        return await self.detect_anomalies(data)