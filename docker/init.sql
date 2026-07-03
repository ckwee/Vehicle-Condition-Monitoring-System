-- TimescaleDB initialization script
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create hypertable for sensor readings
CREATE TABLE IF NOT EXISTS sensor_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    engine_temp FLOAT,
    oil_pressure FLOAT,
    rpm FLOAT,
    speed FLOAT,
    fuel_level FLOAT,
    battery_voltage FLOAT,
    coolant_temp FLOAT,
    transmission_temp FLOAT,
    brake_pad_wear FLOAT,
    tire_pressure FLOAT,
    source VARCHAR(50),
    quality_score FLOAT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score FLOAT
);

-- Convert to hypertable
SELECT create_hypertable('sensor_readings', 'timestamp', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sensor_readings_vehicle_time 
ON sensor_readings (vehicle_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_anomaly 
ON sensor_readings (is_anomaly, timestamp DESC) 
WHERE is_anomaly = TRUE;

-- Create continuous aggregate for hourly statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS bucket,
    vehicle_id,
    AVG(engine_temp) as avg_engine_temp,
    MAX(engine_temp) as max_engine_temp,
    AVG(oil_pressure) as avg_oil_pressure,
    MIN(oil_pressure) as min_oil_pressure,
    AVG(rpm) as avg_rpm,
    AVG(speed) as avg_speed,
    COUNT(*) as reading_count,
    SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomaly_count
FROM sensor_readings
GROUP BY bucket, vehicle_id;

-- Create retention policy (keep raw data for 90 days)
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');

-- Create compression policy
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'vehicle_id',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(100) UNIQUE NOT NULL,
    vehicle_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN',
    title VARCHAR(200),
    message TEXT,
    details JSONB,
    notification_channels JSONB,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on alerts
CREATE INDEX IF NOT EXISTS idx_alerts_vehicle_status 
ON alerts (vehicle_id, status);

CREATE INDEX IF NOT EXISTS idx_alerts_severity_time 
ON alerts (severity, timestamp DESC);

-- Create vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id VARCHAR(50) UNIQUE NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    vin VARCHAR(50) UNIQUE,
    engine_type VARCHAR(50),
    transmission_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert sample vehicles
INSERT INTO vehicles (vehicle_id, make, model, year, engine_type, transmission_type) 
VALUES 
    ('VEH001', 'Toyota', 'Camry', 2023, '2.5L I4', 'Automatic'),
    ('VEH002', 'Ford', 'F-150', 2023, '3.5L V6', 'Automatic'),
    ('VEH003', 'Honda', 'Civic', 2023, '1.5L Turbo', 'CVT'),
    ('VEH004', 'Tesla', 'Model 3', 2023, 'Electric', 'Single Speed'),
    ('VEH005', 'BMW', 'X5', 2023, '3.0L I6', 'Automatic')
ON CONFLICT (vehicle_id) DO NOTHING;