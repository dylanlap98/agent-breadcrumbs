from abc import ABC, abstractmethod
from typing import List, Optional
from ..schemas import AgentAction


class BaseAdapter(ABC):
    """Abstract base class for storage adapters"""

    @abstractmethod
    def log_action(self, action: AgentAction) -> str:
        """Store an agent action and return the action_id"""
        pass

    @abstractmethod
    def get_session_actions(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[AgentAction]:
        """Retrieve all actions for a session"""
        pass

    @abstractmethod
    def get_all_actions(self, limit: Optional[int] = None) -> List[AgentAction]:
        """Retrieve all logged actions"""
        pass
