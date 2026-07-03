# test_system.py
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    from agents.base_agent import BaseAgent
    print("✓ BaseAgent imported successfully")
except Exception as e:
    print(f"✗ BaseAgent import failed: {e}")

try:
    from agents.data_collection_agent import DataCollectionAgent
    print("✓ DataCollectionAgent imported successfully")
except Exception as e:
    print(f"✗ DataCollectionAgent import failed: {e}")

try:
    from agents.preprocessing_agent import PreprocessingAgent
    print("✓ PreprocessingAgent imported successfully")
except Exception as e:
    print(f"✗ PreprocessingAgent import failed: {e}")

try:
    from agents.anomaly_detection_agent import AnomalyDetectionAgent
    print("✓ AnomalyDetectionAgent imported successfully")
except Exception as e:
    print(f"✗ AnomalyDetectionAgent import failed: {e}")

try:
    from agents.diagnosis_agent import DiagnosisAgent
    print("✓ DiagnosisAgent imported successfully")
except Exception as e:
    print(f"✗ DiagnosisAgent import failed: {e}")

try:
    from agents.alert_agent import AlertAgent
    print("✓ AlertAgent imported successfully")
except Exception as e:
    print(f"✗ AlertAgent import failed: {e}")

try:
    from orchestrator import AgentOrchestrator
    print("✓ AgentOrchestrator imported successfully")
except Exception as e:
    print(f"✗ AgentOrchestrator import failed: {e}")

print("\nAll imports tested!")