"""Tests for the agent system."""

import pytest
from datetime import datetime, UTC
from typing import Dict, Any

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

@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initialization."""
    await orchestrator.initialize()
    state = orchestrator.get_state()
    
    assert state["active_agents"] == []
    assert state["task_count"] == 0
    assert "start_time" in state

@pytest.mark.asyncio
async def test_agent_registration(orchestrator, mock_web_surfer):
    """Test agent registration."""
    await orchestrator.initialize()
    orchestrator.register_agent(mock_web_surfer)
    
    state = orchestrator.get_state()
    assert "WebSurfer" in state["active_agents"]
    assert "WebSurfer" in orchestrator.agents

@pytest.mark.asyncio
async def test_task_execution(orchestrator, mock_web_surfer):
    """Test task execution."""
    await orchestrator.initialize()
    await mock_web_surfer.initialize()  # Initialize the mock agent
    orchestrator.register_agent(mock_web_surfer)
    
    task = {
        "type": "web_search",
        "data": {"query": "test query"}
    }
    
    result = await orchestrator.execute(task)
    assert result["status"] == "success"
    assert result["task"] == {"query": "test query"}
    
    # Check task ledger
    task_id = f"task_1"
    task_obj = orchestrator.task_ledger.get_task(task_id)
    assert task_obj is not None
    assert task_obj.status == "completed"
    assert task_obj.assigned_to == "WebSurfer"
    assert task_obj.completed_at is not None

@pytest.mark.asyncio
async def test_task_failure(orchestrator):
    """Test task failure handling."""
    await orchestrator.initialize()
    
    # Try to execute task without registered agent
    task = {
        "type": "web_search",
        "data": {"query": "test query"}
    }
    
    with pytest.raises(ValueError) as exc_info:
        await orchestrator.execute(task)
    assert "No suitable agent found for task" in str(exc_info.value)

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