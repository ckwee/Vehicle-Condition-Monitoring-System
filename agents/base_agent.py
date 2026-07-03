from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

class AgentMessage(BaseModel):
    agent_id: str
    timestamp: datetime
    message_type: str
    payload: Dict[str, Any]
    priority: int = 0

class BaseAgent(ABC):
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.message_queue = []
        self.state = {}
        logger.info(f"Agent {agent_id} initialized")
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    async def send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]):
        msg = AgentMessage(agent_id=self.agent_id, timestamp=datetime.now(), message_type=message_type, payload=payload)
        self.message_queue.append((recipient, msg))
    
    async def receive_messages(self) -> List:
        messages = [(r, m) for r, m in self.message_queue if r == self.agent_id]
        self.message_queue = [(r, m) for r, m in self.message_queue if r != self.agent_id]
        return messages
