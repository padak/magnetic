"""Orchestrator agent implementation."""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio
import os
import logging
import json

from .base import BaseAgent

@dataclass
class Task:
    """Task representation."""
    
    id: str
    type: str
    status: str = "pending"
    priority: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    retries: int = 0
    max_retries: int = 3
    deadline: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=lambda: {
        'cpu_usage': 0.0,
        'memory_usage': 0.0,
        'io_operations': 0
    })

class TaskLedger:
    """Task tracking and management system."""
    
    def __init__(self):
        """Initialize the task ledger."""
        self.tasks: Dict[str, Task] = {}
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
    
    def add_task(self, task: Task) -> None:
        """Add a new task to the ledger."""
        self.tasks[task.id] = task
        if task.dependencies:
            self.task_dependencies[task.id] = task.dependencies
    
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
                self.failed_tasks.pop(task_id, None)
            elif task.status == "failed":
                self.failed_tasks[task_id] = task
                self.active_tasks.pop(task_id, None)
            elif task.status == "in_progress":
                self.active_tasks[task_id] = task
                self.failed_tasks.pop(task_id, None)
    
    def get_pending_tasks(self, priority: Optional[int] = None) -> List[Task]:
        """Get pending tasks, optionally filtered by priority."""
        tasks = [t for t in self.tasks.values() if t.status == "pending"]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        return sorted(tasks, key=lambda t: (
            -t.priority,  # Higher priority first
            not bool(t.deadline),  # Tasks with deadlines first
            t.deadline or datetime.max.replace(tzinfo=timezone.utc),  # Earlier deadlines first
            t.created_at  # Earlier creation time first
        ))
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready for execution (dependencies satisfied)."""
        ready_tasks = []
        for task in self.get_pending_tasks():
            if self.are_dependencies_met(task.id):
                ready_tasks.append(task)
        return ready_tasks
    
    def are_dependencies_met(self, task_id: str) -> bool:
        """Check if all dependencies for a task are completed."""
        if task_id not in self.task_dependencies:
            return True
        return all(
            self.tasks[dep_id].status == "completed"
            for dep_id in self.task_dependencies[task_id]
            if dep_id in self.tasks
        )
    
    def update_metrics(self, task_id: str, metrics: Dict[str, float]) -> None:
        """Update performance metrics for a task."""
        self.performance_metrics[task_id] = metrics
        if task := self.tasks.get(task_id):
            task.metrics.update(metrics)
    
    def get_task_metrics(self, task_id: str) -> Dict[str, float]:
        """Get performance metrics for a task."""
        return self.performance_metrics.get(task_id, {})
    
    def get_failed_tasks_for_retry(self) -> List[Task]:
        """Get failed tasks that can be retried."""
        return [
            task for task in self.failed_tasks.values()
            if task.retries < task.max_retries
        ]

class OrchestratorAgent(BaseAgent):
    """Agent responsible for coordinating other agents and managing tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the orchestrator agent."""
        super().__init__("Orchestrator", config)
        self.task_ledger = TaskLedger()
        self.agents: Dict[str, BaseAgent] = {}
        self.max_concurrent_tasks = 5
        self.running_tasks: Set[asyncio.Task] = set()
    
    async def initialize(self) -> None:
        """Initialize the orchestrator agent."""
        await super().initialize()
        self.update_state({
            "active_agents": [],
            "task_count": 0,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "performance_metrics": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "average_execution_time": 0.0,
                "success_rate": 1.0
            }
        })
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new agent with the orchestrator."""
        self.agents[agent.name] = agent
        active_agents = self.state.get("active_agents", [])
        active_agents.append(agent.name)
        self.update_state({"active_agents": active_agents})
        self.logger.info(f"Registered agent: {agent.name}")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task by delegating to appropriate agent."""
        task_obj = Task(
            id=task.get("id", f"task_{self.state['task_count'] + 1}"),
            type=task["type"],
            data=task.get("data", {}),
            priority=task.get("priority", 1),
            dependencies=task.get("dependencies", []),
            deadline=task.get("deadline"),
            max_retries=task.get("max_retries", 3)
        )
        
        self.task_ledger.add_task(task_obj)
        self.update_state({"task_count": self.state["task_count"] + 1})
        
        # Start task execution
        execution_task = asyncio.create_task(
            self._execute_task(task_obj),
            name=f"task_{task_obj.id}"
        )
        self.running_tasks.add(execution_task)
        execution_task.add_done_callback(self.running_tasks.discard)
        
        try:
            result = await execution_task
            return result
        except Exception as e:
            self.logger.error(f"Task {task_obj.id} failed: {str(e)}")
            raise
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task with retries and error handling."""
        start_time = datetime.now(timezone.utc)
        
        # Find appropriate agent
        agent_name = task.data.get("agent")
        if not agent_name and "type" in task.data:
            agent_mapping = {
                "web_search": "WebSurfer",
                "code_generation": "Coder",
                "file_operation": "FileSurfer"
            }
            agent_name = agent_mapping.get(task.data["type"])
        
        if not agent_name or agent_name not in self.agents:
            raise ValueError(f"No suitable agent found for task: {task.id}")
        
        agent = self.agents[agent_name]
        task.assigned_to = agent_name
        task.status = "in_progress"
        task.started_at = start_time
        self.task_ledger.update_task(task.id, {
            "status": task.status,
            "started_at": task.started_at,
            "assigned_to": task.assigned_to
        })
        
        while task.retries <= task.max_retries:
            try:
                result = await agent.execute(task.data)
                end_time = datetime.now(timezone.utc)
                execution_time = (end_time - start_time).total_seconds()
                
                # Update task metrics
                self.task_ledger.update_metrics(task.id, {
                    "execution_time": execution_time,
                    "retries": task.retries
                })
                
                # Update task status
                task.status = "completed"
                task.completed_at = end_time
                task.result = result
                task.execution_time = execution_time
                self.task_ledger.update_task(task.id, {
                    "status": task.status,
                    "completed_at": task.completed_at,
                    "result": result,
                    "execution_time": execution_time
                })
                
                # Update agent state metrics
                metrics = self.state["performance_metrics"]
                metrics["tasks_completed"] += 1
                metrics["average_execution_time"] = (
                    (metrics["average_execution_time"] * (metrics["tasks_completed"] - 1) + execution_time)
                    / metrics["tasks_completed"]
                )
                metrics["success_rate"] = (
                    metrics["tasks_completed"] /
                    (metrics["tasks_completed"] + metrics["tasks_failed"])
                )
                self.update_state({"performance_metrics": metrics})
                
                return result
                
            except Exception as e:
                task.retries += 1
                task.error_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                    "retry_count": task.retries
                })
                
                if task.retries > task.max_retries:
                    task.status = "failed"
                    self.state["performance_metrics"]["tasks_failed"] += 1
                    self.task_ledger.update_task(task.id, {
                        "status": task.status,
                        "error_history": task.error_history
                    })
                    raise
                
                # Exponential backoff for retries
                await asyncio.sleep(2 ** task.retries)
    
    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel with dependency management."""
        task_objects = []
        for task in tasks:
            task_obj = Task(
                id=task.get("id", f"task_{self.state['task_count'] + 1}"),
                type=task["type"],
                data=task.get("data", {}),
                priority=task.get("priority", 1),
                dependencies=task.get("dependencies", []),
                deadline=task.get("deadline"),
                max_retries=task.get("max_retries", 3)
            )
            self.task_ledger.add_task(task_obj)
            task_objects.append(task_obj)
            self.state["task_count"] += 1
        
        results = []
        pending_tasks = task_objects.copy()
        
        while pending_tasks:
            # Get tasks that are ready to execute
            ready_tasks = [
                task for task in pending_tasks
                if self.task_ledger.are_dependencies_met(task.id)
            ]
            
            if not ready_tasks:
                # No tasks are ready, wait for some to complete
                await asyncio.sleep(0.1)
                continue
            
            # Execute ready tasks in parallel
            execution_tasks = []
            for task in ready_tasks[:self.max_concurrent_tasks]:
                execution_task = asyncio.create_task(
                    self._execute_task(task),
                    name=f"task_{task.id}"
                )
                self.running_tasks.add(execution_task)
                execution_task.add_done_callback(self.running_tasks.discard)
                execution_tasks.append(execution_task)
                pending_tasks.remove(task)
            
            # Wait for tasks to complete
            batch_results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results
    
    async def cleanup(self) -> None:
        """Clean up orchestrator and all registered agents."""
        # Cancel any running tasks
        for task in self.running_tasks:
            task.cancel()
        
        # Wait for tasks to finish
        if self.running_tasks:
            await asyncio.wait(self.running_tasks)
        
        # Cleanup agents
        for agent in self.agents.values():
            await agent.cleanup()
        self.agents.clear()
        
        await super().cleanup() 