"""Orchestrator agent implementation using Magentic-One framework."""

from typing import Dict, List, Optional, Any
import asyncio
import os
from datetime import datetime, UTC
from dataclasses import dataclass, field

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

@dataclass
class TaskMetrics:
    """Task performance metrics."""
    execution_time: float = 0.0
    retries: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    io_operations: int = 0

class OrchestratorM1:
    """Orchestrator agent using Magentic-One framework."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Orchestrator agent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.client = OpenAIChatCompletionClient(
            model=self.config.get('model', 'gpt-4-turbo-preview'),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.code_executor = LocalCommandLineCodeExecutor()
        self.m1 = MagenticOne(
            client=self.client,
            code_executor=self.code_executor
        )
        
        # Initialize state
        self.state = {
            "active_agents": [],
            "task_count": 0,
            "start_time": datetime.now(UTC).isoformat(),
            "performance_metrics": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "average_execution_time": 0.0,
                "success_rate": 1.0
            }
        }
        
        # Task tracking
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 5)
        
    async def initialize(self) -> None:
        """Initialize the orchestrator agent."""
        # Nothing to initialize for now
        pass
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel any running tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        if self.active_tasks:
            await asyncio.wait(list(self.active_tasks.values()))
        
        self.active_tasks.clear()
        self.tasks.clear()
        self.state["active_agents"] = []
        
    async def execute(self, task: dict) -> dict:
        """Execute a task and track its status."""
        task_id = f"task_{self.state['task_count'] + 1}"
        task_info = {
            "id": task_id,
            "type": task["type"],
            "status": "in_progress",
            "started_at": datetime.now(),
            "data": task.get("data", {}),
            "error": None,
            "result": None,
            "metrics": TaskMetrics()
        }
        self.tasks[task_id] = task_info
        self.state["task_count"] += 1

        try:
            result = await self._execute_task(task_id, task)
            task_info["status"] = "completed"
            task_info["result"] = result
            task_info["completed_at"] = datetime.now()
            return result
        except Exception as e:
            task_info["status"] = "failed"
            task_info["error"] = str(e)
            task_info["completed_at"] = datetime.now()
            self.state["performance_metrics"]["tasks_failed"] += 1
            raise

    async def _execute_task(self, task_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with retries and error handling."""
        start_time = datetime.now(UTC)
        max_retries = task.get("max_retries", 3)
        retry_count = 0
        
        self.tasks[task_id]["status"] = "in_progress"
        self.tasks[task_id]["started_at"] = start_time.isoformat()
        
        while retry_count <= max_retries:
            try:
                # Convert task to Magentic-One format
                m1_task = {
                    "task_type": task["type"],
                    "instructions": task.get("data", {}).get("instructions", ""),
                    "parameters": task.get("data", {}),
                    "context": {
                        "task_id": task_id,
                        "retry_count": retry_count
                    }
                }
                
                # Execute task
                result = await self.m1.run_stream(m1_task)
                
                # Update metrics
                end_time = datetime.now(UTC)
                execution_time = (end_time - start_time).total_seconds()
                
                self.tasks[task_id].update({
                    "status": "completed",
                    "completed_at": end_time.isoformat(),
                    "result": result,
                    "metrics": TaskMetrics(
                        execution_time=execution_time,
                        retries=retry_count
                    )
                })
                
                # Update performance metrics
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
                
                return result
                
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    # Don't update failure metrics here, let execute() handle it
                    self.tasks[task_id]["status"] = "failed"
                    self.tasks[task_id]["error"] = str(e)
                    raise
                
                # Add error to history
                error_history = self.tasks[task_id].get("error_history", [])
                error_history.append({
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error": str(e),
                    "retry_count": retry_count
                })
                self.tasks[task_id]["error_history"] = error_history
                
                # Exponential backoff
                await asyncio.sleep(2 ** retry_count)
                
    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel with concurrency control.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            List of task results
        """
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        async def execute_with_semaphore(task: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.execute(task)
        
        # Execute tasks with controlled concurrency
        return await asyncio.gather(
            *(execute_with_semaphore(task) for task in tasks),
            return_exceptions=True
        )
        
    def get_task_status(self, task_id: str) -> dict:
        """Get status information for a specific task."""
        return self.tasks.get(task_id, {})
        
    def get_active_tasks(self) -> list:
        """Get list of currently active tasks."""
        return [
            task for task in self.tasks.values()
            if task["status"] == "in_progress"
        ]
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        return self.state["performance_metrics"].copy() 