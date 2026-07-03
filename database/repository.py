from sqlalchemy import create_engine, and_, or_, func, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from loguru import logger
import os
from dotenv import load_dotenv

from models import (
    Base, Vehicle, SensorReading, Anomaly, Diagnosis, 
    Alert, MaintenanceRecord, NotificationLog, AlertSeverity, AlertStatus
)

load_dotenv()

class DatabaseRepository:
    """Database repository for vehicle monitoring system"""
    
    def __init__(self, connection_string: Optional[str] = None):
        if connection_string is None:
            # Build connection string from environment variables
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "vehicle_monitoring")
            db_user = os.getenv("POSTGRES_USER", "admin")
            db_password = os.getenv("POSTGRES_PASSWORD", "password")
            
            connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with context management"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()
    
    # Vehicle Operations
    def register_vehicle(self, vehicle_data: Dict[str, Any]) -> Vehicle:
        """Register a new vehicle"""
        with self.get_session() as session:
            vehicle = Vehicle(**vehicle_data)
            session.add(vehicle)
            session.flush()
            return vehicle
    
    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get vehicle by ID"""
        with self.get_session() as session:
            return session.query(Vehicle).filter(
                Vehicle.vehicle_id == vehicle_id
            ).first()
    
    def get_active_vehicles(self) -> List[Vehicle]:
        """Get all active vehicles"""
        with self.get_session() as session:
            return session.query(Vehicle).filter(
                Vehicle.status == "active"
            ).all()
    
    # Sensor Reading Operations
    def store_sensor_reading(self, reading_data: Dict[str, Any]) -> SensorReading:
        """Store a sensor reading"""
        with self.get_session() as session:
            reading = SensorReading(**reading_data)
            session.add(reading)
            session.flush()
            return reading
    
    def store_sensor_readings_bulk(self, readings: List[Dict[str, Any]]) -> int:
        """Store multiple sensor readings in bulk"""
        with self.get_session() as session:
            readings_obj = [SensorReading(**r) for r in readings]
            session.bulk_save_objects(readings_obj)
            return len(readings_obj)
    
    def get_sensor_readings(
        self,
        vehicle_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """Get sensor readings for a vehicle within time range"""
        with self.get_session() as session:
            query = session.query(SensorReading).filter(
                SensorReading.vehicle_id == vehicle_id,
                SensorReading.timestamp >= start_time
            )
            
            if end_time:
                query = query.filter(SensorReading.timestamp <= end_time)
            
            query = query.order_by(SensorReading.timestamp.desc()).limit(limit)
            
            df = pd.read_sql(query.statement, session.bind)
            return df
    
    def get_latest_readings(self, vehicle_id: str, limit: int = 100) -> pd.DataFrame:
        """Get latest sensor readings for a vehicle"""
        with self.get_session() as session:
            query = session.query(SensorReading).filter(
                SensorReading.vehicle_id == vehicle_id
            ).order_by(SensorReading.timestamp.desc()).limit(limit)
            
            df = pd.read_sql(query.statement, session.bind)
            return df
    
    # Anomaly Operations
    def store_anomaly(self, anomaly_data: Dict[str, Any]) -> Anomaly:
        """Store detected anomaly"""
        with self.get_session() as session:
            anomaly = Anomaly(**anomaly_data)
            session.add(anomaly)
            session.flush()
            return anomaly
    
    def get_anomalies(
        self,
        vehicle_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Anomaly]:
        """Get anomalies with optional filters"""
        with self.get_session() as session:
            query = session.query(Anomaly)
            
            if vehicle_id:
                query = query.filter(Anomaly.vehicle_id == vehicle_id)
            if severity:
                query = query.filter(Anomaly.severity == severity)
            if start_time:
                query = query.filter(Anomaly.timestamp >= start_time)
            
            return query.order_by(Anomaly.timestamp.desc()).limit(limit).all()
    
    # Diagnosis Operations
    def store_diagnosis(self, diagnosis_data: Dict[str, Any]) -> Diagnosis:
        """Store diagnosis"""
        with self.get_session() as session:
            diagnosis = Diagnosis(**diagnosis_data)
            session.add(diagnosis)
            session.flush()
            return diagnosis
    
    def get_diagnoses(
        self,
        vehicle_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Diagnosis]:
        """Get diagnoses for a vehicle"""
        with self.get_session() as session:
            query = session.query(Diagnosis)
            if vehicle_id:
                query = query.filter(Diagnosis.vehicle_id == vehicle_id)
            return query.order_by(Diagnosis.timestamp.desc()).limit(limit).all()
    
    # Alert Operations
    def store_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Store alert"""
        with self.get_session() as session:
            alert = Alert(**alert_data)
            session.add(alert)
            session.flush()
            return alert
    
    def update_alert_status(
        self,
        alert_id: str,
        status: AlertStatus,
        updated_by: Optional[str] = None
    ) -> bool:
        """Update alert status"""
        with self.get_session() as session:
            alert = session.query(Alert).filter(Alert.alert_id == alert_id).first()
            if alert:
                alert.status = status
                if status == AlertStatus.ACKNOWLEDGED:
                    alert.acknowledged_by = updated_by
                    alert.acknowledged_at = datetime.utcnow()
                elif status == AlertStatus.RESOLVED:
                    alert.resolved_by = updated_by
                    alert.resolved_at = datetime.utcnow()
                return True
            return False
    
    def get_open_alerts(
        self,
        vehicle_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get open alerts"""
        with self.get_session() as session:
            query = session.query(Alert).filter(
                Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED])
            )
            
            if vehicle_id:
                query = query.filter(Alert.vehicle_id == vehicle_id)
            if severity:
                query = query.filter(Alert.severity == severity)
            
            return query.order_by(Alert.timestamp.desc()).all()
    
    # Maintenance Operations
    def store_maintenance_record(self, record_data: Dict[str, Any]) -> MaintenanceRecord:
        """Store maintenance record"""
        with self.get_session() as session:
            record = MaintenanceRecord(**record_data)
            session.add(record)
            session.flush()
            return record
    
    def get_maintenance_history(self, vehicle_id: str) -> List[MaintenanceRecord]:
        """Get maintenance history for a vehicle"""
        with self.get_session() as session:
            return session.query(MaintenanceRecord).filter(
                MaintenanceRecord.vehicle_id == vehicle_id
            ).order_by(MaintenanceRecord.timestamp.desc()).all()
    
    # Notification Operations
    def log_notification(self, notification_data: Dict[str, Any]) -> NotificationLog:
        """Log a notification"""
        with self.get_session() as session:
            notification = NotificationLog(**notification_data)
            session.add(notification)
            session.flush()
            return notification
    
    # Analytics Queries
    def get_vehicle_health_score(self, vehicle_id: str) -> Dict[str, Any]:
        """Calculate vehicle health score based on recent data"""
        with self.get_session() as session:
            # Get recent anomalies
            recent_anomalies = session.query(Anomaly).filter(
                Anomaly.vehicle_id == vehicle_id,
                Anomaly.timestamp >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            # Get open alerts
            open_alerts = session.query(Alert).filter(
                Alert.vehicle_id == vehicle_id,
                Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED])
            ).all()
            
            # Calculate health score
            score = 100
            
            # Deduct for anomalies by severity
            severity_deductions = {
                AlertSeverity.CRITICAL: 20,
                AlertSeverity.HIGH: 10,
                AlertSeverity.MEDIUM: 5,
                AlertSeverity.LOW: 2
            }
            
            for anomaly in recent_anomalies:
                if anomaly.severity in severity_deductions:
                    score -= severity_deductions[anomaly.severity]
            
            # Deduct for open alerts
            for alert in open_alerts:
                if alert.severity in severity_deductions:
                    score -= severity_deductions[alert.severity] * 0.5
            
            score = max(0, min(100, score))
            
            return {
                "vehicle_id": vehicle_id,
                "health_score": score,
                "recent_anomalies": len(recent_anomalies),
                "open_alerts": len(open_alerts),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_fleet_statistics(self) -> Dict[str, Any]:
        """Get fleet-wide statistics"""
        with self.get_session() as session:
            # Vehicle counts
            total_vehicles = session.query(Vehicle).count()
            active_vehicles = session.query(Vehicle).filter(
                Vehicle.status == "active"
            ).count()
            
            # Alert statistics
            alert_stats = session.query(
                Alert.severity,
                func.count(Alert.id).label('count')
            ).filter(
                Alert.timestamp >= datetime.utcnow() - timedelta(days=7)
            ).group_by(Alert.severity).all()
            
            # Anomaly statistics
            anomaly_stats = session.query(
                Anomaly.sensor_name,
                func.count(Anomaly.id).label('count')
            ).filter(
                Anomaly.timestamp >= datetime.utcnow() - timedelta(days=7)
            ).group_by(Anomaly.sensor_name).all()
            
            return {
                "total_vehicles": total_vehicles,
                "active_vehicles": active_vehicles,
                "alert_statistics": {s.value: c for s, c in alert_stats},
                "anomaly_statistics": {s: c for s, c in anomaly_stats},
                "timestamp": datetime.utcnow().isoformat()
            }