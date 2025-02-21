"""Orchestrator agent implementation."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, UTC

from .base import BaseAgent

@dataclass
class Task:
    """Task representation."""
    
    id: str
    type: str
    status: str = "pending"
    priority: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None

class TaskLedger:
    """Task tracking and management system."""
    
    def __init__(self):
        """Initialize the task ledger."""
        self.tasks: Dict[str, Task] = {}
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
    
    def add_task(self, task: Task) -> None:
        """Add a new task to the ledger."""
        self.tasks[task.id] = task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Update a task's attributes."""
        if task := self.tasks.get(task_id):
            for key, value in updates.items():
                setattr(task, key, value)
            
            # Move task to appropriate collection based on status
            if task.status == "completed":
                self.completed_tasks[task_id] = task
                self.active_tasks.pop(task_id, None)
            elif task.status == "in_progress":
                self.active_tasks[task_id] = task
    
    def get_pending_tasks(self, priority: Optional[int] = None) -> List[Task]:
        """Get pending tasks, optionally filtered by priority."""
        tasks = [t for t in self.tasks.values() if t.status == "pending"]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        return sorted(tasks, key=lambda t: (t.priority, t.created_at))

class OrchestratorAgent(BaseAgent):
    """Agent responsible for coordinating other agents and managing tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the orchestrator agent."""
        super().__init__("Orchestrator", config)
        self.task_ledger = TaskLedger()
        self.agents: Dict[str, BaseAgent] = {}
    
    async def initialize(self) -> None:
        """Initialize the orchestrator agent."""
        await super().initialize()
        self.update_state({
            "active_agents": [],
            "task_count": 0,
            "start_time": datetime.now(UTC).isoformat()
        })
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new agent with the orchestrator.
        
        Args:
            agent: The agent to register
        """
        self.agents[agent.name] = agent
        active_agents = self.state.get("active_agents", [])
        active_agents.append(agent.name)
        self.update_state({"active_agents": active_agents})
        self.logger.info(f"Registered agent: {agent.name}")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task by delegating to appropriate agent.
        
        Args:
            task: The task to execute
            
        Returns:
            Dict containing the task result
        """
        await super().execute(task)
        
        task_obj = Task(
            id=task.get("id", f"task_{self.state['task_count'] + 1}"),
            type=task["type"],
            data=task.get("data", {}),
            priority=task.get("priority", 1)
        )
        
        self.task_ledger.add_task(task_obj)
        self.update_state({"task_count": self.state["task_count"] + 1})
        
        # Find appropriate agent for task
        agent_name = task.get("agent")
        if not agent_name and "type" in task:
            # Map task type to agent if not explicitly specified
            agent_mapping = {
                "web_search": "WebSurfer",
                "code_generation": "Coder",
                "file_operation": "FileSurfer"
            }
            agent_name = agent_mapping.get(task["type"])
        
        if not agent_name or agent_name not in self.agents:
            raise ValueError(f"No suitable agent found for task: {task}")
        
        agent = self.agents[agent_name]
        task_obj.assigned_to = agent_name
        task_obj.status = "in_progress"
        task_obj.started_at = datetime.now(UTC)
        self.task_ledger.update_task(task_obj.id, {
            "status": task_obj.status,
            "started_at": task_obj.started_at,
            "assigned_to": task_obj.assigned_to
        })
        
        try:
            result = await agent.execute(task_obj.data)
            task_obj.status = "completed"
            task_obj.completed_at = datetime.now(UTC)
            task_obj.result = result
            self.task_ledger.update_task(task_obj.id, {
                "status": task_obj.status,
                "completed_at": task_obj.completed_at,
                "result": result
            })
            return result
        except Exception as e:
            task_obj.status = "failed"
            task_obj.result = {"error": str(e)}
            self.task_ledger.update_task(task_obj.id, {
                "status": task_obj.status,
                "result": task_obj.result
            })
            raise
    
    async def cleanup(self) -> None:
        """Clean up orchestrator and all registered agents."""
        for agent in self.agents.values():
            await agent.cleanup()
        self.agents.clear()
        await super().cleanup() 