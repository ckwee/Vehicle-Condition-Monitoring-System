# agents/diagnosis_agent.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

# Use relative import
from .base_agent import BaseAgent

class DiagnosisAgent(BaseAgent):
    """Agent responsible for diagnosing the root cause of anomalies using AI"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("diagnosis_agent", config)
        self.rules_db = self.load_diagnostic_rules()
        self.use_llm = config.get("use_llm", False)
        self.openai_api_key = config.get("openai_api_key")
        logger.info(f"DiagnosisAgent initialized (LLM={'enabled' if self.use_llm else 'disabled'})")
        
    def load_diagnostic_rules(self) -> Dict[str, Any]:
        """Load diagnostic rules database"""
        return {
            "engine_temp": {
                "high": {
                    "possible_causes": [
                        "Coolant leak or low coolant level",
                        "Thermostat malfunction",
                        "Radiator fan failure",
                        "Water pump failure"
                    ],
                    "severity": "HIGH",
                    "recommended_actions": [
                        "Check coolant level immediately",
                        "Inspect for visible leaks",
                        "Monitor engine temperature closely",
                        "Schedule maintenance if persists"
                    ]
                },
                "low": {
                    "possible_causes": [
                        "Faulty temperature sensor",
                        "Thermostat stuck open",
                        "Cold weather operation"
                    ],
                    "severity": "MEDIUM",
                    "recommended_actions": [
                        "Verify sensor readings",
                        "Check thermostat operation",
                        "Allow engine to warm up properly"
                    ]
                }
            },
            "oil_pressure": {
                "low": {
                    "possible_causes": [
                        "Low oil level",
                        "Oil pump failure",
                        "Clogged oil filter",
                        "Worn engine bearings"
                    ],
                    "severity": "CRITICAL",
                    "recommended_actions": [
                        "Stop engine immediately if pressure is very low",
                        "Check oil level",
                        "Inspect for oil leaks",
                        "Schedule immediate maintenance"
                    ]
                },
                "high": {
                    "possible_causes": [
                        "Clogged oil passages",
                        "Faulty pressure relief valve",
                        "Incorrect oil viscosity"
                    ],
                    "severity": "MEDIUM",
                    "recommended_actions": [
                        "Check oil type and viscosity",
                        "Inspect oil filter",
                        "Monitor pressure trends"
                    ]
                }
            },
            "battery_voltage": {
                "low": {
                    "possible_causes": [
                        "Alternator failure",
                        "Battery degradation",
                        "Loose or corroded connections",
                        "Excessive electrical load"
                    ],
                    "severity": "HIGH",
                    "recommended_actions": [
                        "Check alternator output",
                        "Test battery health",
                        "Inspect electrical connections",
                        "Reduce electrical load if possible"
                    ]
                },
                "high": {
                    "possible_causes": [
                        "Voltage regulator failure",
                        "Overcharging condition",
                        "Faulty alternator"
                    ],
                    "severity": "HIGH",
                    "recommended_actions": [
                        "Check voltage regulator",
                        "Test charging system",
                        "Inspect for electrical system damage"
                    ]
                }
            },
            "coolant_temp": {
                "high": {
                    "possible_causes": [
                        "Coolant leak",
                        "Radiator blockage",
                        "Cooling fan failure",
                        "Head gasket failure"
                    ],
                    "severity": "CRITICAL",
                    "recommended_actions": [
                        "Stop vehicle if overheating severely",
                        "Check coolant level (when cool)",
                        "Inspect radiator and hoses",
                        "Check for white exhaust smoke"
                    ]
                }
            },
            "transmission_temp": {
                "high": {
                    "possible_causes": [
                        "Low transmission fluid",
                        "Transmission fluid degradation",
                        "Torque converter issues",
                        "Transmission cooler failure"
                    ],
                    "severity": "HIGH",
                    "recommended_actions": [
                        "Check transmission fluid level and condition",
                        "Inspect transmission cooler lines",
                        "Avoid heavy loads until diagnosed",
                        "Schedule transmission service"
                    ]
                }
            }
        }
    
    async def rule_based_diagnosis(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform rule-based diagnosis"""
        diagnoses = []
        anomaly_details = anomaly_data.get("anomaly_scores", {}).get("details", [])
        
        for detail in anomaly_details:
            sensor = detail["sensor"]
            value = detail["value"]
            mean = detail["mean"]
            
            if value > mean:
                direction = "high"
            else:
                direction = "low"
            
            sensor_rules = self.rules_db.get(sensor, {}).get(direction)
            
            if sensor_rules:
                diagnoses.append({
                    "sensor": sensor,
                    "current_value": round(value, 2),
                    "normal_range": f"{mean * 0.8:.1f} - {mean * 1.2:.1f}",
                    "deviation": f"{((value - mean) / mean * 100):.1f}%",
                    "severity": sensor_rules["severity"],
                    "possible_causes": sensor_rules["possible_causes"],
                    "recommended_actions": sensor_rules["recommended_actions"],
                    "diagnosis_confidence": "HIGH" if abs(value - mean) / mean > 0.2 else "MEDIUM"
                })
        
        return {
            "diagnoses": diagnoses,
            "total_anomalies": len(diagnoses),
            "critical_issues": any(d["severity"] == "CRITICAL" for d in diagnoses),
            "diagnosis_method": "rule_based"
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process anomaly data and provide diagnosis"""
        try:
            vehicle_id = data.get("vehicle_id", "Unknown")
            logger.info(f"Diagnosing anomalies for vehicle {vehicle_id}")
            
            rule_diagnosis = await self.rule_based_diagnosis(data)
            
            result = {
                **data,
                "diagnosis": rule_diagnosis,
                "diagnosis_timestamp": datetime.now().isoformat(),
                "diagnosed_by": f"Agent: {self.agent_id}"
            }
            
            await self.send_message(
                "alert_agent",
                "diagnosis_complete",
                result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in diagnosis: {str(e)}")
            return {"status": "error", "message": str(e)}