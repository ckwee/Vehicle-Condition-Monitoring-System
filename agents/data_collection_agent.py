# agents/data_collection_agent.py
import asyncio
import random
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List
from loguru import logger

# Use relative import
from .base_agent import BaseAgent

class DataCollectionAgent(BaseAgent):
    """Agent responsible for collecting vehicle sensor data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("data_collection_agent", config)
        self.vehicle_ids = config.get("vehicle_ids", ["VEH001", "VEH002", "VEH003"])
        self.sampling_rate = config.get("sampling_rate", 1)
        self.sensors = [
            "engine_temp", "oil_pressure", "rpm", "speed", 
            "fuel_level", "battery_voltage", "coolant_temp",
            "transmission_temp", "brake_pad_wear", "tire_pressure"
        ]
        logger.info(f"DataCollectionAgent monitoring vehicles: {self.vehicle_ids}")
        
    async def generate_sensor_data(self, vehicle_id: str) -> Dict[str, Any]:
        """Generate realistic sensor data with occasional anomalies"""
        timestamp = datetime.now()
        
        base_values = {
            "engine_temp": 90 + np.random.normal(0, 2),
            "oil_pressure": 40 + np.random.normal(0, 3),
            "rpm": 2500 + np.random.normal(0, 200),
            "speed": 60 + np.random.normal(0, 10),
            "fuel_level": 65 + np.random.normal(0, 1),
            "battery_voltage": 12.6 + np.random.normal(0, 0.1),
            "coolant_temp": 85 + np.random.normal(0, 1.5),
            "transmission_temp": 75 + np.random.normal(0, 2),
            "brake_pad_wear": 30 + np.random.normal(0, 0.5),
            "tire_pressure": 32 + np.random.normal(0, 0.5)
        }
        
        # Introduce anomalies occasionally (5% chance per reading)
        if random.random() < 0.05:
            anomaly_sensor = random.choice(self.sensors)
            logger.debug(f"Introducing anomaly in {anomaly_sensor} for {vehicle_id}")
            
            if anomaly_sensor == "engine_temp":
                base_values["engine_temp"] += random.choice([30, -20])
            elif anomaly_sensor == "oil_pressure":
                base_values["oil_pressure"] += random.choice([20, -15])
            elif anomaly_sensor == "battery_voltage":
                base_values["battery_voltage"] += random.choice([2, -3])
            elif anomaly_sensor == "coolant_temp":
                base_values["coolant_temp"] += random.choice([25, -15])
            elif anomaly_sensor == "transmission_temp":
                base_values["transmission_temp"] += random.choice([30, -10])
        
        sensor_data = {
            "vehicle_id": vehicle_id,
            "timestamp": timestamp,
            "source": "simulated",
            **base_values
        }
        
        return sensor_data
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data from all vehicles"""
        all_vehicle_data = []
        
        for vehicle_id in self.vehicle_ids:
            try:
                sensor_data = await self.generate_sensor_data(vehicle_id)
                all_vehicle_data.append(sensor_data)
                
                # Send data to preprocessing agent
                await self.send_message(
                    "preprocessing_agent",
                    "new_sensor_data",
                    sensor_data
                )
            except Exception as e:
                logger.error(f"Error collecting data for {vehicle_id}: {str(e)}")
        
        logger.debug(f"Collected data for {len(all_vehicle_data)} vehicles")
        
        return {
            "status": "success",
            "vehicles_processed": len(self.vehicle_ids),
            "timestamp": datetime.now().isoformat(),
            "data": all_vehicle_data
        }