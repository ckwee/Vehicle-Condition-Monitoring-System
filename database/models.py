from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, 
    Boolean, ForeignKey, Index, Text, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from datetime import datetime
import enum

Base = declarative_base()

class AlertSeverity(enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AlertStatus(enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(String(50), unique=True, nullable=False, index=True)
    make = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    vin = Column(String(50), unique=True)
    engine_type = Column(String(50))
    transmission_type = Column(String(50))
    status = Column(String(20), default="active")
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="vehicle")
    alerts = relationship("Alert", back_populates="vehicle")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Sensor values
    engine_temp = Column(Float)
    oil_pressure = Column(Float)
    rpm = Column(Float)
    speed = Column(Float)
    fuel_level = Column(Float)
    battery_voltage = Column(Float)
    coolant_temp = Column(Float)
    transmission_temp = Column(Float)
    brake_pad_wear = Column(Float)
    tire_pressure = Column(Float)
    
    # Derived features
    engine_temp_rate = Column(Float)
    oil_pressure_rate = Column(Float)
    rpm_rate = Column(Float)
    speed_rate = Column(Float)
    
    # Metadata
    source = Column(String(50))  # simulated, obd2, api, mqtt
    quality_score = Column(Float)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float)
    metadata = Column(JSONB)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="sensor_readings")
    
    __table_args__ = (
        Index("idx_sensor_readings_vehicle_time", "vehicle_id", "timestamp"),
    )

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    sensor_name = Column(String(50), nullable=False)
    sensor_value = Column(Float)
    expected_value = Column(Float)
    deviation_percentage = Column(Float)
    z_score = Column(Float)
    anomaly_score = Column(Float)
    detection_method = Column(String(50))
    severity = Column(Enum(AlertSeverity))
    is_confirmed = Column(Boolean, default=False)
    metadata = Column(JSONB)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="anomalies")
    
    __table_args__ = (
        Index("idx_anomalies_vehicle_time", "vehicle_id", "timestamp"),
        Index("idx_anomalies_sensor_severity", "sensor_name", "severity"),
    )

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anomaly_id = Column(UUID(as_uuid=True), ForeignKey("anomalies.id"), nullable=False)
    vehicle_id = Column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Diagnosis details
    diagnosis_method = Column(String(50))  # rule_based, llm, hybrid
    confidence_score = Column(Float)
    severity = Column(Enum(AlertSeverity))
    
    # Root cause analysis
    primary_cause = Column(Text)
    possible_causes = Column(JSONB)
    risk_assessment = Column(JSONB)
    
    # Recommendations
    immediate_actions = Column(JSONB)
    maintenance_recommendations = Column(JSONB)
    estimated_repair_time = Column(String(100))
    estimated_cost_range = Column(String(100))
    
    # LLM Analysis
    llm_analysis = Column(JSONB)
    llm_model = Column(String(50))
    
    metadata = Column(JSONB)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="diagnoses")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    vehicle_id = Column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey("diagnoses.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    
    title = Column(String(200))
    message = Column(Text)
    details = Column(JSONB)
    
    # Notification tracking
    notification_channels = Column(JSONB)
    notification_sent = Column(Boolean, default=False)
    notification_timestamp = Column(DateTime(timezone=True))
    
    # Response tracking
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime(timezone=True))
    
    metadata = Column(JSONB)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="alerts")
    
    __table_args__ = (
        Index("idx_alerts_vehicle_status", "vehicle_id", "status"),
        Index("idx_alerts_severity_time", "severity", "timestamp"),
    )

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey("diagnoses.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    maintenance_type = Column(String(100))  # preventive, corrective, predictive
    description = Column(Text)
    performed_by = Column(String(200))
    cost = Column(Float)
    parts_replaced = Column(JSONB)
    duration_hours = Column(Float)
    notes = Column(Text)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_records")

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(100), ForeignKey("alerts.alert_id"), nullable=False)
    channel = Column(String(50))  # email, sms, push, telegram
    recipient = Column(String(200))
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20))  # sent, delivered, failed
    error_message = Column(Text)
    metadata = Column(JSONB)