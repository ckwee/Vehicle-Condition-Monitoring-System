import obd
from obd import OBDStatus, OBDCommand
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
from loguru import logger
import serial
import time

class OBD2Connector:
    """Real OBD2 connector for vehicle data collection"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 38400):
        self.port = port
        self.baudrate = baudrate
        self.connection: Optional[obd.OBD] = None
        self.supported_commands = []
        self.sensor_mapping = {
            "engine_temp": obd.commands.COOLANT_TEMP,
            "rpm": obd.commands.RPM,
            "speed": obd.commands.SPEED,
            "fuel_level": obd.commands.FUEL_LEVEL,
            "oil_pressure": None,  # Not standard OBD-II
            "battery_voltage": obd.commands.CONTROL_MODULE_VOLTAGE,
            "coolant_temp": obd.commands.COOLANT_TEMP,
            "transmission_temp": None,  # Manufacturer specific
            "brake_pad_wear": None,  # Not available via OBD-II
            "tire_pressure": None  # Requires TPMS system
        }
        
    async def connect(self) -> bool:
        """Connect to OBD2 adapter"""
        try:
            self.connection = obd.OBD(
                portstr=self.port,
                baudrate=self.baudrate,
                fast=True,
                timeout=30
            )
            
            if self.connection.status() == OBDStatus.CAR_CONNECTED:
                logger.info(f"Connected to vehicle via OBD2 on {self.port}")
                await self._get_supported_commands()
                return True
            else:
                logger.error(f"Failed to connect to vehicle: {self.connection.status()}")
                return False
                
        except Exception as e:
            logger.error(f"OBD2 connection error: {str(e)}")
            return False
    
    async def _get_supported_commands(self):
        """Get list of supported OBD commands"""
        if self.connection:
            self.supported_commands = [
                cmd for cmd in self.sensor_mapping.values() 
                if cmd and self.connection.supports(cmd)
            ]
            logger.info(f"Supported commands: {len(self.supported_commands)}")
    
    async def read_sensor_data(self) -> Dict[str, Any]:
        """Read current sensor values"""
        if not self.connection or self.connection.status() != OBDStatus.CAR_CONNECTED:
            logger.warning("Not connected to vehicle")
            return {}
        
        sensor_data = {
            "timestamp": datetime.utcnow(),
            "source": "obd2"
        }
        
        for sensor_name, command in self.sensor_mapping.items():
            if command and self.connection.supports(command):
                try:
                    response = self.connection.query(command)
                    if response and not response.is_null():
                        sensor_data[sensor_name] = response.value.magnitude
                    else:
                        sensor_data[sensor_name] = None
                except Exception as e:
                    logger.error(f"Error reading {sensor_name}: {str(e)}")
                    sensor_data[sensor_name] = None
            else:
                sensor_data[sensor_name] = None
        
        return sensor_data
    
    async def read_dtc_codes(self) -> List[Dict[str, Any]]:
        """Read Diagnostic Trouble Codes"""
        if not self.connection:
            return []
        
        try:
            dtcs = self.connection.query(obd.commands.GET_DTC)
            if dtcs and not dtcs.is_null():
                return [
                    {
                        "code": dtc[0],
                        "description": dtc[1],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    for dtc in dtcs.value
                ]
        except Exception as e:
            logger.error(f"Error reading DTCs: {str(e)}")
        
        return []
    
    async def disconnect(self):
        """Disconnect from OBD2 adapter"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from OBD2")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

# Example usage
async def example_obd2_usage():
    async with OBD2Connector(port="/dev/ttyUSB0") as connector:
        if await connector.connect():
            while True:
                data = await connector.read_sensor_data()
                print(f"Sensor Data: {data}")
                
                dtcs = await connector.read_dtc_codes()
                if dtcs:
                    print(f"DTCs: {dtcs}")
                
                await asyncio.sleep(1)