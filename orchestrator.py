# orchestrator.py - Fixed with proper imports
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from loguru import logger
import sys
import os

# Use direct imports instead of package imports
from agents.data_collection_agent import DataCollectionAgent
from agents.preprocessing_agent import PreprocessingAgent
from agents.anomaly_detection_agent import AnomalyDetectionAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.alert_agent import AlertAgent

class AgentOrchestrator:
    """Orchestrates all agents in the vehicle monitoring system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agents = {}
        self.running = False
        self.data_store = {
            "sensor_data": [],
            "anomalies": [],
            "diagnoses": [],
            "alerts": []
        }
        
        # Initialize agents
        self.initialize_agents()
        logger.info("AgentOrchestrator initialized successfully")
        
    def initialize_agents(self):
        """Initialize all agents"""
        try:
            self.agents["data_collection"] = DataCollectionAgent(
                self.config.get("data_collection", {})
            )
            logger.info("Data Collection Agent initialized")
            
            self.agents["preprocessing"] = PreprocessingAgent(
                self.config.get("preprocessing", {})
            )
            logger.info("Preprocessing Agent initialized")
            
            self.agents["anomaly_detection"] = AnomalyDetectionAgent(
                self.config.get("anomaly_detection", {})
            )
            logger.info("Anomaly Detection Agent initialized")
            
            self.agents["diagnosis"] = DiagnosisAgent(
                self.config.get("diagnosis", {})
            )
            logger.info("Diagnosis Agent initialized")
            
            self.agents["alert"] = AlertAgent(
                self.config.get("alert", {})
            )
            logger.info("Alert Agent initialized")
            
            logger.info("All agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    async def run_pipeline(self):
        """Run the complete monitoring pipeline"""
        self.running = True
        logger.info("Pipeline started")
        
        iteration = 0
        while self.running:
            try:
                iteration += 1
                if iteration % 10 == 0:
                    logger.info(f"Pipeline iteration {iteration}")
                
                # Step 1: Collect data
                collection_result = await self.agents["data_collection"].process({})
                
                # Step 2: Process messages between agents
                await self.process_agent_messages()
                
                # Small delay to control sampling rate
                await asyncio.sleep(self.config.get("sampling_interval", 1))
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Pipeline error: {str(e)}")
                await asyncio.sleep(1)
    
    async def process_agent_messages(self):
        """Route messages between agents"""
        try:
            for agent_name, agent in self.agents.items():
                messages = await agent.receive_messages()
                
                for recipient, msg in messages:
                    if msg.message_type == "new_sensor_data":
                        # Route to preprocessing
                        result = await self.agents["preprocessing"].process(msg.payload)
                        
                    elif msg.message_type == "preprocessed_data":
                        # Route to anomaly detection
                        result = await self.agents["anomaly_detection"].process(msg.payload)
                        
                        # Store results
                        self.store_result("sensor_data", result)
                        
                    elif msg.message_type == "anomaly_detected":
                        # Route to diagnosis
                        result = await self.agents["diagnosis"].process(msg.payload)
                        
                        # Store anomalies
                        self.store_result("anomalies", msg.payload)
                        
                    elif msg.message_type == "diagnosis_complete":
                        # Route to alert
                        result = await self.agents["alert"].process(msg.payload)
                        
                        # Store diagnoses and alerts
                        self.store_result("diagnoses", msg.payload)
                        self.store_result("alerts", result)
                        
        except Exception as e:
            logger.error(f"Error processing messages: {str(e)}")
    
    def store_result(self, category: str, data: Dict[str, Any]):
        """Store results in memory"""
        if category in self.data_store:
            self.data_store[category].append(data)
            
            # Keep data manageable
            if len(self.data_store[category]) > 10000:
                self.data_store[category] = self.data_store[category][-5000:]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        try:
            # Convert sensor data to DataFrame for time series
            sensor_df = pd.DataFrame(self.data_store["sensor_data"])
            
            return {
                "sensor_data": sensor_df,
                "anomalies": self.data_store["anomalies"][-100:],
                "diagnoses": self.data_store["diagnoses"][-50:],
                "alerts": self.data_store["alerts"][-50:],
                "agent_status": {name: "RUNNING" for name in self.agents.keys()},
                "pipeline_status": "ACTIVE" if self.running else "STOPPED"
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {
                "sensor_data": pd.DataFrame(),
                "anomalies": [],
                "diagnoses": [],
                "alerts": [],
                "agent_status": {},
                "pipeline_status": "ERROR"
            }
    
    async def run_pipeline_single(self):
        """Run a single iteration of the pipeline"""
        try:
            # Collect data
            await self.agents["data_collection"].process({})
            # Process messages
            await self.process_agent_messages()
        except Exception as e:
            logger.error(f"Single pipeline iteration error: {str(e)}")
    
    async def stop(self):
        """Stop the orchestration"""
        self.running = False
        logger.info("Orchestrator stopped")