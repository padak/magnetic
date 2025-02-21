"""Example script demonstrating the agent system."""

import asyncio
import logging
from magnetic.agents.base import BaseAgent
from magnetic.agents.orchestrator import OrchestratorAgent
from magnetic.utils.logging import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

class WebSurferAgent(BaseAgent):
    """A simple WebSurfer agent for demonstration purposes."""
    
    async def initialize(self):
        """Initialize the agent's state."""
        logger.info(f"[INIT] Starting initialization of WebSurfer agent (id: {id(self)})")
        logger.info(f"[INIT] Current state before update: {self.state}")
        
        self.state.update({
            'searches_performed': 0,
            'last_search_query': None,
            'search_results': []
        })
        
        logger.info(f"[INIT] State after update: {self.state}")
        await super().initialize()
        logger.info(f"[INIT] Initialization completed, final state: {self.state}")
        logger.info("WebSurfer agent initialized")
    
    async def execute(self, task):
        """Execute a web search task."""
        logger.info(f"[EXEC] Starting task execution (agent id: {id(self)})")
        logger.info(f"[EXEC] Current state at execution start: {self.state}")
        
        query = task.get('query', '')
        if not query:
            return {'error': 'No search query provided'}
        
        # Simulate web search
        logger.info(f"[EXEC] Performing web search for: {query}")
        
        try:
            logger.info(f"[EXEC] Attempting to update searches_performed. Current value: {self.state.get('searches_performed')}")
            self.state['searches_performed'] += 1
            logger.info(f"[EXEC] Successfully updated searches_performed. New state: {self.state}")
        except Exception as e:
            logger.error(f"[EXEC] Error updating state: {str(e)}")
            logger.error(f"[EXEC] Current state: {self.state}")
            raise
        
        self.state['last_search_query'] = query
        
        # Simulate search results
        mock_results = [
            f"Result 1 for {query}",
            f"Result 2 for {query}",
            f"Result 3 for {query}"
        ]
        self.state['search_results'] = mock_results
        
        logger.info(f"[EXEC] Final state after execution: {self.state}")
        return {
            'status': 'success',
            'results': mock_results,
            'state': self.state
        }

async def main():
    """Main function to demonstrate the agent system."""
    try:
        # Initialize the orchestrator
        logger.info("[MAIN] Creating orchestrator")
        orchestrator = OrchestratorAgent()
        await orchestrator.initialize()
        
        # Create and register the WebSurfer agent
        logger.info("[MAIN] Creating WebSurfer agent")
        web_surfer = WebSurferAgent(name="WebSurfer")
        logger.info(f"[MAIN] Created WebSurfer agent (id: {id(web_surfer)})")
        
        logger.info("[MAIN] Initializing WebSurfer agent")
        await web_surfer.initialize()
        logger.info(f"[MAIN] WebSurfer agent state after initialization: {web_surfer.state}")
        
        logger.info("[MAIN] Registering WebSurfer agent with orchestrator")
        orchestrator.register_agent(web_surfer)
        
        # Execute some test tasks
        search_tasks = [
            {
                'type': 'web_search',
                'data': {'query': 'weather in San Francisco'}
            },
            {
                'type': 'web_search',
                'data': {'query': 'best restaurants in New York'}
            },
            {
                'type': 'web_search',
                'data': {'query': 'tourist attractions in Paris'}
            }
        ]
        
        for task in search_tasks:
            logger.info(f"\n[MAIN] Executing task: {task}")
            result = await orchestrator.execute(task)
            logger.info(f"[MAIN] Task result: {result}")
            logger.info(f"[MAIN] WebSurfer agent state: {web_surfer.state}")
        
        # Cleanup
        await orchestrator.cleanup()
        logger.info("[MAIN] Test completed successfully")
        
    except Exception as e:
        logger.error(f"[MAIN] Error during test execution: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main()) 