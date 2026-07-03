# main.py - Fixed version
import asyncio
import sys
import os
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import AgentOrchestrator

async def main():
    """Main entry point for the vehicle monitoring system"""
    
    # Configuration
    config = {
        "sampling_interval": 1,  # seconds
        "data_collection": {
            "vehicle_ids": ["VEH001", "VEH002", "VEH003"],
            "sampling_rate": 1
        },
        "preprocessing": {
            "window_size": 100,
            "outlier_threshold": 3
        },
        "anomaly_detection": {
            "anomaly_threshold": -0.1,
            "training_size": 50,
            "retrain_frequency": 20
        },
        "diagnosis": {
            "use_llm": False,  # Set to True if you have OpenAI API key
            "openai_api_key": "your-api-key-here"
        },
        "alert": {
            "notification_endpoints": {
                "email": ["maintenance@example.com"],
                "sms": ["+1234567890"]
            }
        }
    }
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(config)
    
    print("🚗 Vehicle Condition Monitoring System")
    print("=" * 50)
    print("Starting agents...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print("=" * 50)
    
    # Start the pipeline
    try:
        await orchestrator.run_pipeline()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        await orchestrator.stop()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        await orchestrator.stop()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())