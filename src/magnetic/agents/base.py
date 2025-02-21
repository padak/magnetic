"""Base agent implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

from ..config.settings import Config
from ..utils.logging import get_logger

class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, name: str, config: Optional[Config] = None):
        """Initialize the base agent.
        
        Args:
            name: The name of the agent
            config: Optional configuration instance
        """
        self.name = name
        self.config = config or Config.get_instance()
        self.logger = get_logger(f"agent.{name.lower()}")
        
        # Initialize agent state
        self.state: Dict[str, Any] = {}
        self.is_initialized = False
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent. Must be implemented by subclasses."""
        self.is_initialized = True
        self.logger.info(f"Agent {self.name} initialized")
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task. Must be implemented by subclasses.
        
        Args:
            task: The task to execute
            
        Returns:
            Dict containing the task result
        """
        if not self.is_initialized:
            raise RuntimeError(f"Agent {self.name} not initialized")
        
    async def cleanup(self) -> None:
        """Clean up agent resources. Can be overridden by subclasses."""
        self.state.clear()
        self.is_initialized = False
        self.logger.info(f"Agent {self.name} cleaned up")
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current agent state."""
        return self.state.copy()
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """Update the agent state.
        
        Args:
            updates: Dictionary of state updates
        """
        self.state.update(updates)
        self.logger.debug(f"Updated state: {updates}")
    
    def clear_state(self) -> None:
        """Clear the agent state."""
        self.state.clear()
        self.logger.debug("State cleared") 