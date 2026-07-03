# agents/alert_agent.py
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

# Use relative import
from .base_agent import BaseAgent

class AlertAgent(BaseAgent):
    """Agent responsible for managing alerts and notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("alert_agent", config)
        self.alerts = []
        self.alert_thresholds = {
            "CRITICAL": {"immediate": True, "cooldown": 300},
            "HIGH": {"immediate": False, "cooldown": 600},
            "MEDIUM": {"immediate": False, "cooldown": 1800},
            "LOW": {"immediate": False, "cooldown": 3600}
        }
        logger.info("AlertAgent initialized")
        
    async def prioritize_alert(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine alert priority based on diagnosis"""
        severity_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        
        max_severity = "LOW"
        for diag in diagnosis.get("diagnosis", {}).get("diagnoses", []):
            if diag["severity"] in severity_levels:
                if severity_levels.index(diag["severity"]) < severity_levels.index(max_severity):
                    max_severity = diag["severity"]
        
        return {
            "severity": max_severity,
            "requires_immediate_action": max_severity == "CRITICAL",
            "notification_channels": self.get_notification_channels(max_severity)
        }
    
    def get_notification_channels(self, severity: str) -> List[str]:
        """Determine notification channels based on severity"""
        channels = {
            "CRITICAL": ["dashboard", "email", "sms", "push_notification"],
            "HIGH": ["dashboard", "email", "push_notification"],
            "MEDIUM": ["dashboard", "email"],
            "LOW": ["dashboard"]
        }
        return channels.get(severity, ["dashboard"])
    
    async def create_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert from diagnosis data"""
        priority_info = await self.prioritize_alert(data)
        
        alert = {
            "alert_id": f"ALT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{data.get('vehicle_id', 'UNKNOWN')}",
            "vehicle_id": data.get("vehicle_id"),
            "timestamp": datetime.now().isoformat(),
            "severity": priority_info["severity"],
            "message": self.generate_alert_message(data),
            "diagnosis_summary": data.get("diagnosis", {}),
            "anomaly_details": data.get("anomaly_scores", {}).get("details", []),
            "status": "OPEN",
            "requires_immediate_action": priority_info["requires_immediate_action"],
            "notification_channels": priority_info["notification_channels"]
        }
        
        self.alerts.append(alert)
        
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        logger.info(f"Alert created: {alert['alert_id']} - Severity: {alert['severity']}")
        
        return alert
    
    def generate_alert_message(self, data: Dict[str, Any]) -> str:
        """Generate human-readable alert message"""
        vehicle_id = data.get("vehicle_id", "Unknown")
        diagnoses = data.get("diagnosis", {}).get("diagnoses", [])
        
        if not diagnoses:
            return f"Anomaly detected in vehicle {vehicle_id}"
        
        message_parts = [f"Vehicle {vehicle_id}:"]
        
        for diag in diagnoses[:3]:
            message_parts.append(f"{diag['sensor']} ({diag['severity']})")
        
        if len(diagnoses) > 3:
            message_parts.append(f"and {len(diagnoses) - 3} more...")
        
        message = " ".join(message_parts)
        
        if data.get("diagnosis", {}).get("critical_issues"):
            message += " - CRITICAL ISSUES DETECTED!"
        
        return message
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process diagnosis and create alerts"""
        try:
            alert = await self.create_alert(data)
            logger.info(f"Alert processed: {alert['alert_id']} for vehicle {alert['vehicle_id']}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_alerts(self, vehicle_id: str = None, severity: str = None, limit: int = 50) -> List[Dict]:
        """Retrieve alerts with optional filtering"""
        filtered_alerts = self.alerts
        
        if vehicle_id:
            filtered_alerts = [a for a in filtered_alerts if a.get("vehicle_id") == vehicle_id]
        
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.get("severity") == severity]
        
        return filtered_alerts[-limit:]
