# Migration Guide: Moving to Magentic-One

## Overview

This guide outlines the process of migrating our current agent-based system to use Microsoft's Magentic-One framework through AutoGen. The migration will provide better agent coordination, standardized communication, and access to AutoGen's robust ecosystem.

## Current vs New Architecture

### Current Architecture
```python
class OrchestratorAgent(BaseAgent):
    def __init__(self):
        self.task_ledger = TaskLedger()
        self.agents = {}
        self.max_concurrent_tasks = 5
```

### New Architecture (Magentic-One)
```python
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_ext.models.openai import OpenAIChatCompletionClient

class EnhancedOrchestrator:
    def __init__(self):
        self.model_client = OpenAIChatCompletionClient(model="gpt-4o")
        self.m1 = MagenticOne(client=self.model_client)
```

## Key Changes

1. Dependencies
```python
# Add to requirements.txt
autogen-agentchat>=0.2.0
autogen-ext[magentic-one,openai]>=0.2.0
pyautogen>=0.2.0
```

2. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright dependencies
playwright install --with-deps chromium
```

3. Configuration
```python
# Environment variables (.env)
OPENAI_API_KEY=sk-your-key-here
```

## Migration Steps

### 1. Task Management

#### Before:
```python
async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
    task_obj = Task(
        id=task.get("id", f"task_{self.state['task_count'] + 1}"),
        type=task["type"],
        data=task.get("data", {})
    )
    self.task_ledger.add_task(task_obj)
```

#### After:
```python
async def execute_task(self, task: str) -> Dict[str, Any]:
    return await self.m1.run_stream(task=task)
```

### 2. Agent Registration

#### Before:
```python
def register_agent(self, agent: BaseAgent) -> None:
    self.agents[agent.name] = agent
    self.state["active_agents"].append(agent.name)
```

#### After:
Agents are automatically managed by Magentic-One:
```python
# Agents are created and managed internally by MagenticOne
m1 = MagenticOne(client=model_client)
```

### 3. Task Execution

#### Before:
```python
async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    task_objects = []
    for task in tasks:
        task_obj = Task(...)
        self.task_ledger.add_task(task_obj)
        task_objects.append(task_obj)
```

#### After:
```python
async def execute_tasks(self, tasks: List[str]) -> List[Dict[str, Any]]:
    return await asyncio.gather(
        *(self.m1.run_stream(task=task) for task in tasks)
    )
```

## Example Usage

```python
#!/usr/bin/env python
"""Example using Magentic-One for travel planning."""

import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_agentchat.ui import Console

# Load environment variables
load_dotenv()

async def main():
    # Initialize OpenAI client
    client = OpenAIChatCompletionClient(
        model="gpt-4-turbo-preview",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Create MagenticOne instance
    m1 = MagenticOne(client=client)

    # Define task
    task = """
    Plan a family trip to Boston for summer 2024. Consider:
    1. Activities for all ages
    2. Accommodation options
    3. Transportation
    4. Budget estimates
    5. Daily itinerary
    """

    # Execute task with streaming output
    await Console(m1.run_stream(task=task))

if __name__ == "__main__":
    asyncio.run(main())
```

## Benefits of Migration

1. **Simplified Architecture**
   - Reduced boilerplate code
   - Automatic agent coordination
   - Built-in task management

2. **Enhanced Capabilities**
   - Access to AutoGen's agent ecosystem
   - Better error handling
   - Improved parallel execution
   - Built-in streaming support

3. **Better Integration**
   - Standardized communication protocols
   - Access to multiple LLM providers
   - Built-in monitoring and logging

4. **Future-Proof**
   - Regular updates from Microsoft
   - Community support
   - Standardized best practices

## Migration Checklist

- [ ] Update dependencies in requirements.txt
- [ ] Set up environment variables
- [ ] Install Playwright dependencies
- [ ] Refactor Orchestrator implementation
- [ ] Update test suite
- [ ] Migrate existing tasks
- [ ] Update documentation
- [ ] Test all functionality
- [ ] Monitor performance

## Notes

1. The example in `test_magnetic_one.py` uses the new Magentic-One concepts:
   - Uses `MagenticOne` class directly
   - Implements streaming with `Console`
   - Uses modern GPT-4 Turbo model
   - Proper environment variable handling
   - Proper cleanup of async tasks

2. Key Differences:
   - No manual agent management needed
   - Simpler task definition (plain text vs structured dict)
   - Built-in streaming support
   - Automatic resource cleanup

## Best Practices

1. **Environment Management**
   - Use .env files for configuration
   - Validate API keys before use
   - Use virtual environments

2. **Error Handling**
   - Implement proper try-except blocks
   - Clean up resources in finally blocks
   - Handle async task cancellation

3. **Task Definition**
   - Use clear, structured prompts
   - Include all necessary context
   - Break complex tasks into subtasks

4. **Resource Management**
   - Implement proper cleanup
   - Cancel pending tasks
   - Close connections properly

## Support and Resources

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Magentic-One Guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html)
- [GitHub Repository](https://github.com/microsoft/autogen/tree/main/python/packages/autogen-agentchat)
