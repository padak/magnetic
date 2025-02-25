"""Tests for the agent system."""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import asyncio
from unittest.mock import AsyncMock

from magnetic.agents.base import BaseAgent
from magnetic.agents.orchestrator import OrchestratorAgent, Task, TaskLedger

class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, name: str):
        """Initialize mock agent."""
        super().__init__(name)
        self.executed_tasks = []
    
    async def initialize(self) -> None:
        """Initialize the mock agent."""
        await super().initialize()
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mock task."""
        await super().execute(task)
        self.executed_tasks.append(task)
        return {"status": "success", "task": task}

@pytest.fixture
def orchestrator():
    """Create an orchestrator agent for testing."""
    return OrchestratorAgent()

@pytest.fixture
def mock_web_surfer():
    """Create a mock WebSurfer agent."""
    return MockAgent("WebSurfer")

@pytest.fixture
def mock_coder():
    """Create a mock Coder agent."""
    return MockAgent("Coder")

@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = AsyncMock(spec=BaseAgent)
    agent.name = "MockAgent"
    agent.execute = AsyncMock(return_value={"result": "success"})
    agent.cleanup = AsyncMock()
    return agent

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator agent initialization."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    
    assert orchestrator.state["active_agents"] == []
    assert orchestrator.state["task_count"] == 0
    assert "start_time" in orchestrator.state
    assert "performance_metrics" in orchestrator.state
    assert orchestrator.state["performance_metrics"]["tasks_completed"] == 0
    assert orchestrator.state["performance_metrics"]["tasks_failed"] == 0

@pytest.mark.asyncio
async def test_agent_registration(mock_agent):
    """Test agent registration."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    
    orchestrator.register_agent(mock_agent)
    assert mock_agent.name in orchestrator.agents
    assert mock_agent.name in orchestrator.state["active_agents"]

@pytest.mark.asyncio
async def test_task_execution(mock_agent):
    """Test basic task execution."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    orchestrator.register_agent(mock_agent)
    
    task = {
        "type": "test",
        "data": {"agent": "MockAgent"},
        "priority": 2
    }
    
    result = await orchestrator.execute(task)
    assert result == {"result": "success"}
    
    # Verify task ledger
    task_id = f"task_1"
    task_obj = orchestrator.task_ledger.get_task(task_id)
    assert task_obj.status == "completed"
    assert task_obj.priority == 2
    assert task_obj.assigned_to == "MockAgent"
    assert task_obj.result == {"result": "success"}
    assert task_obj.execution_time is not None

@pytest.mark.asyncio
async def test_task_execution_with_retry(mock_agent):
    """Test task execution with retry on failure."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    orchestrator.register_agent(mock_agent)
    
    # Make the agent fail twice then succeed
    mock_agent.execute = AsyncMock(side_effect=[
        Exception("First failure"),
        Exception("Second failure"),
        {"result": "success"}
    ])
    
    task = {
        "type": "test",
        "data": {"agent": "MockAgent"},
        "max_retries": 3
    }
    
    result = await orchestrator.execute(task)
    assert result == {"result": "success"}
    
    # Verify task ledger
    task_id = f"task_1"
    task_obj = orchestrator.task_ledger.get_task(task_id)
    assert task_obj.status == "completed"
    assert task_obj.retries == 2
    assert len(task_obj.error_history) == 2
    assert "First failure" in task_obj.error_history[0]["error"]
    assert "Second failure" in task_obj.error_history[1]["error"]

@pytest.mark.asyncio
async def test_parallel_task_execution(mock_agent):
    """Test parallel task execution with dependencies."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    orchestrator.register_agent(mock_agent)
    
    tasks = [
        {
            "id": "task1",
            "type": "test",
            "data": {"agent": "MockAgent"},
            "priority": 1
        },
        {
            "id": "task2",
            "type": "test",
            "data": {"agent": "MockAgent"},
            "priority": 2,
            "dependencies": ["task1"]
        },
        {
            "id": "task3",
            "type": "test",
            "data": {"agent": "MockAgent"},
            "priority": 3,
            "dependencies": ["task2"]
        }
    ]
    
    results = await orchestrator.execute_parallel(tasks)
    assert len(results) == 3
    assert all(r == {"result": "success"} for r in results)
    
    # Verify execution order
    task1 = orchestrator.task_ledger.get_task("task1")
    task2 = orchestrator.task_ledger.get_task("task2")
    task3 = orchestrator.task_ledger.get_task("task3")
    
    assert task1.started_at < task2.started_at
    assert task2.started_at < task3.started_at

@pytest.mark.asyncio
async def test_task_prioritization():
    """Test task prioritization with deadlines."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    
    now = datetime.now(timezone.utc)
    future = now + timedelta(hours=1)
    far_future = now + timedelta(hours=2)
    
    tasks = [
        Task(id="task1", type="test", priority=1),
        Task(id="task2", type="test", priority=2, deadline=far_future),
        Task(id="task3", type="test", priority=1, deadline=future),
        Task(id="task4", type="test", priority=2)
    ]
    
    for task in tasks:
        orchestrator.task_ledger.add_task(task)
    
    pending_tasks = orchestrator.task_ledger.get_pending_tasks()
    task_ids = [task.id for task in pending_tasks]
    
    # Should be ordered by: priority (high to low), has_deadline, deadline, created_at
    assert task_ids == ["task2", "task4", "task3", "task1"]

@pytest.mark.asyncio
async def test_performance_metrics(mock_agent):
    """Test performance metrics tracking."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    orchestrator.register_agent(mock_agent)
    
    # Execute multiple tasks
    tasks = [
        {"type": "test", "data": {"agent": "MockAgent"}},
        {"type": "test", "data": {"agent": "MockAgent"}}
    ]
    
    await orchestrator.execute_parallel(tasks)
    
    metrics = orchestrator.state["performance_metrics"]
    assert metrics["tasks_completed"] == 2
    assert metrics["tasks_failed"] == 0
    assert metrics["average_execution_time"] > 0
    assert metrics["success_rate"] == 1.0

@pytest.mark.asyncio
async def test_cleanup(mock_agent):
    """Test cleanup with running tasks."""
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    orchestrator.register_agent(mock_agent)
    
    # Start a long-running task
    mock_agent.execute = AsyncMock(side_effect=lambda x: asyncio.sleep(1))
    task = {"type": "test", "data": {"agent": "MockAgent"}}
    
    # Start task but don't wait for it
    asyncio.create_task(orchestrator.execute(task))
    
    # Immediate cleanup should cancel the task
    await orchestrator.cleanup()
    
    assert len(orchestrator.running_tasks) == 0
    assert mock_agent.cleanup.called

def test_task_ledger():
    """Test TaskLedger functionality."""
    ledger = TaskLedger()
    
    # Create test task
    task = Task(
        id="test_1",
        type="test",
        priority=1,
        data={"test": "data"}
    )
    
    # Add task
    ledger.add_task(task)
    assert task.id in ledger.tasks
    
    # Update task
    ledger.update_task(task.id, {"status": "in_progress"})
    assert task.status == "in_progress"
    assert task.id in ledger.active_tasks
    
    # Complete task
    ledger.update_task(task.id, {"status": "completed"})
    assert task.status == "completed"
    assert task.id in ledger.completed_tasks
    assert task.id not in ledger.active_tasks
    
    # Get pending tasks
    pending = ledger.get_pending_tasks()
    assert len(pending) == 0  # All tasks completed 