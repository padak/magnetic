"""Tests for Magentic-One Orchestrator implementation."""

import pytest
import pytest_asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch
import asyncio

from magnetic.agents.orchestrator_m1 import OrchestratorM1, TaskMetrics

@pytest_asyncio.fixture
async def orchestrator():
    """Create an Orchestrator instance for testing."""
    with patch('magnetic.agents.orchestrator_m1.OpenAIChatCompletionClient') as mock_client_class:
        # Configure mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Create orchestrator instance
        orchestrator = OrchestratorM1()
        await orchestrator.initialize()
        try:
            yield orchestrator
        finally:
            await orchestrator.cleanup()

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orchestrator = OrchestratorM1()
    await orchestrator.initialize()
    
    assert orchestrator.state["active_agents"] == []
    assert orchestrator.state["task_count"] == 0
    assert "start_time" in orchestrator.state
    assert "performance_metrics" in orchestrator.state
    assert orchestrator.state["performance_metrics"]["tasks_completed"] == 0
    assert orchestrator.state["performance_metrics"]["tasks_failed"] == 0

@pytest.mark.asyncio
async def test_task_execution(orchestrator):
    """Test basic task execution."""
    # Mock Magentic-One response
    expected_result = {"status": "success", "data": "test result"}
    orchestrator.m1.run_stream = AsyncMock(return_value=expected_result)
    
    task = {
        "type": "test_task",
        "data": {
            "instructions": "Test instruction",
            "parameters": {"test": "value"}
        }
    }
    
    result = await orchestrator.execute(task)
    
    assert result == expected_result
    assert orchestrator.state["task_count"] == 1
    assert orchestrator.state["performance_metrics"]["tasks_completed"] == 1
    
    # Verify task tracking
    task_id = f"task_1"
    task_info = orchestrator.get_task_status(task_id)
    assert task_info["status"] == "completed"
    assert task_info["type"] == "test_task"
    assert isinstance(task_info["metrics"], TaskMetrics)
    assert task_info["metrics"].execution_time > 0

@pytest.mark.asyncio
async def test_task_execution_with_retry(orchestrator):
    """Test task execution with retry on failure."""
    # Mock Magentic-One to fail twice then succeed
    orchestrator.m1.run_stream = AsyncMock(side_effect=[
        Exception("First failure"),
        Exception("Second failure"),
        {"status": "success"}
    ])
    
    task = {
        "type": "test_task",
        "max_retries": 3,
        "data": {"test": "value"}
    }
    
    result = await orchestrator.execute(task)
    
    assert result == {"status": "success"}
    
    # Verify task tracking
    task_id = f"task_1"
    task_info = orchestrator.get_task_status(task_id)
    assert task_info["status"] == "completed"
    assert task_info["metrics"].retries == 2
    assert len(task_info["error_history"]) == 2
    assert "First failure" in task_info["error_history"][0]["error"]
    assert "Second failure" in task_info["error_history"][1]["error"]

@pytest.mark.asyncio
async def test_task_execution_failure(orchestrator):
    """Test task execution failure handling."""
    # Mock Magentic-One to always fail
    orchestrator.m1.run_stream = AsyncMock(side_effect=Exception("Permanent failure"))
    
    task = {
        "type": "test_task",
        "max_retries": 1,
        "data": {"test": "value"}
    }
    
    with pytest.raises(Exception) as exc_info:
        await orchestrator.execute(task)
    assert "Permanent failure" in str(exc_info.value)
    
    # Verify task tracking
    task_id = f"task_1"
    task_info = orchestrator.get_task_status(task_id)
    assert task_info["status"] == "failed"
    assert task_info["error"] == "Permanent failure"
    assert orchestrator.state["performance_metrics"]["tasks_failed"] == 1

@pytest.mark.asyncio
async def test_parallel_execution(orchestrator):
    """Test parallel task execution."""
    # Mock Magentic-One responses
    results = [
        {"status": "success", "id": 1},
        {"status": "success", "id": 2},
        {"status": "success", "id": 3}
    ]
    orchestrator.m1.run_stream = AsyncMock(side_effect=results)
    
    tasks = [
        {"type": "test_task", "data": {"id": 1}},
        {"type": "test_task", "data": {"id": 2}},
        {"type": "test_task", "data": {"id": 3}}
    ]
    
    parallel_results = await orchestrator.execute_parallel(tasks)
    
    assert len(parallel_results) == 3
    assert all(r["status"] == "success" for r in parallel_results)
    assert orchestrator.state["task_count"] == 3
    assert orchestrator.state["performance_metrics"]["tasks_completed"] == 3

@pytest.mark.asyncio
async def test_cleanup(orchestrator):
    """Test cleanup with running tasks."""
    # Mock a long-running task
    orchestrator.m1.run_stream = AsyncMock(side_effect=lambda x: asyncio.sleep(1))
    
    # Start a task but don't wait for it
    task = {"type": "test_task", "data": {"test": "value"}}
    asyncio.create_task(orchestrator.execute(task))
    
    # Immediate cleanup should cancel the task
    await orchestrator.cleanup()
    
    assert len(orchestrator.active_tasks) == 0
    assert len(orchestrator.tasks) == 0
    assert orchestrator.state["active_agents"] == []

@pytest.mark.asyncio
async def test_metrics_tracking(orchestrator):
    """Test performance metrics tracking."""
    # Mock successful task execution
    orchestrator.m1.run_stream = AsyncMock(return_value={"status": "success"})
    
    # Execute two tasks
    tasks = [
        {"type": "test_task", "data": {"id": 1}},
        {"type": "test_task", "data": {"id": 2}}
    ]
    
    await orchestrator.execute_parallel(tasks)
    
    metrics = orchestrator.get_metrics()
    assert metrics["tasks_completed"] == 2
    assert metrics["tasks_failed"] == 0
    assert metrics["average_execution_time"] > 0
    assert metrics["success_rate"] == 1.0

@pytest.mark.asyncio
async def test_task_status_tracking(orchestrator):
    """Test task status tracking functionality."""
    # Mock Magentic-One to delay execution
    async def delayed_response(*args, **kwargs):
        await asyncio.sleep(0.2)  # Longer delay to ensure we can check status
        return {"status": "success"}
    orchestrator.m1.run_stream = AsyncMock(side_effect=delayed_response)
    
    task = {"type": "test_task", "data": {"test": "value"}}
    
    # Start task execution
    task_execution = asyncio.create_task(orchestrator.execute(task))
    
    # Give the task time to start
    await asyncio.sleep(0.1)
    
    # Check active tasks
    active_tasks = orchestrator.get_active_tasks()
    assert len(active_tasks) == 1
    assert active_tasks[0]["status"] == "in_progress"
    
    # Wait for completion
    await task_execution
    
    # Verify final status
    task_id = f"task_1"
    task_info = orchestrator.get_task_status(task_id)
    assert task_info["status"] == "completed"
    assert "started_at" in task_info
    assert "completed_at" in task_info 