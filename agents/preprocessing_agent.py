# agents/preprocessing_agent.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger

# Use relative import
from .base_agent import BaseAgent

class PreprocessingAgent(BaseAgent):
    """Agent responsible for cleaning and preprocessing sensor data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("preprocessing_agent", config)
        self.data_buffer = {}
        self.window_size = config.get("window_size", 100)
        self.outlier_threshold = config.get("outlier_threshold", 3)
        logger.info(f"PreprocessingAgent initialized with window_size={self.window_size}")
        
    async def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate sensor data"""
        vehicle_id = data.get("vehicle_id")
        
        if not vehicle_id:
            logger.error("No vehicle_id in data")
            return data
        
        if vehicle_id not in self.data_buffer:
            self.data_buffer[vehicle_id] = []
        
        self.data_buffer[vehicle_id].append(data)
        
        if len(self.data_buffer[vehicle_id]) > self.window_size:
            self.data_buffer[vehicle_id].pop(0)
        
        return data
    
    async def calculate_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived features from raw sensor data"""
        vehicle_id = data.get("vehicle_id")
        features = data.copy()
        
        if vehicle_id in self.data_buffer and len(self.data_buffer[vehicle_id]) > 1:
            prev_data = self.data_buffer[vehicle_id][-2]
            
            for sensor in self.sensors:
                if sensor in prev_data and sensor in data:
                    current_val = data.get(sensor)
                    prev_val = prev_data.get(sensor)
                    
                    if current_val is not None and prev_val is not None:
                        time_diff = (data["timestamp"] - prev_data["timestamp"]).total_seconds()
                        
                        if time_diff > 0:
                            features[f"{sensor}_rate"] = (current_val - prev_val) / time_diff
        
        return features
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean incoming sensor data"""
        try:
            cleaned_data = await self.clean_data(data)
            enriched_data = await self.calculate_features(cleaned_data)
            
            await self.send_message(
                "anomaly_detection_agent",
                "preprocessed_data",
                enriched_data
            )
            
            return {
                "status": "success",
                "vehicle_id": data.get("vehicle_id"),
                "features_calculated": True,
                "data": enriched_data
            }
            
        except Exception as e:
            logger.error(f"Error in preprocessing: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    @property
    def sensors(self) -> List[str]:
        return [
            "engine_temp", "oil_pressure", "rpm", "speed",
            "fuel_level", "battery_voltage", "coolant_temp",
            "transmission_temp", "brake_pad_wear", "tire_pressure"
        ]