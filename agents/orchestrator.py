async def run_pipeline_single(self):
    """Run a single iteration of the pipeline"""
    try:
        # Collect data
        await self.agents["data_collection"].process({})
        # Process messages
        await self.process_agent_messages()
    except Exception as e:
        logger.error(f"Single pipeline iteration error: {str(e)}")