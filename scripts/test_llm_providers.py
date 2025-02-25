#!/usr/bin/env python
"""Test script for LLM provider switching."""

import os
import asyncio
import json
from dotenv import load_dotenv
import argparse
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.magnetic.config.llm_config import LLMConfig
from src.magnetic.agents.orchestrator_m1 import OrchestratorM1, LLMClientFactory

async def test_provider(provider: str):
    """Test a specific LLM provider.
    
    Args:
        provider: The LLM provider to test
    """
    print(f"\n=== Testing {provider.upper()} Provider ===")
    
    # Override environment variable
    os.environ["LLM_PROVIDER"] = provider
    
    # Get configuration
    config = LLMConfig.get_config(provider)
    print(f"Configuration: {json.dumps(config, indent=2)}")
    
    # Create client
    client = LLMClientFactory.create_client(provider, config)
    print(f"Client: {client.__class__.__name__}")
    
    # Create orchestrator
    orchestrator = OrchestratorM1()
    await orchestrator.initialize()
    
    # Test with a simple task
    print("\nExecuting test task...")
    try:
        result = await orchestrator.execute({
            "type": "test",
            "data": {
                "query": "What is the capital of France?"
            }
        })
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Clean up
    await orchestrator.cleanup()

async def main():
    """Main function."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test LLM providers")
    parser.add_argument(
        "--provider", 
        choices=["openai", "anthropic", "azure", "all"], 
        default="all",
        help="LLM provider to test"
    )
    args = parser.parse_args()
    
    if args.provider == "all":
        # Test all providers
        for provider in ["openai", "anthropic", "azure"]:
            try:
                await test_provider(provider)
            except Exception as e:
                print(f"Error testing {provider}: {str(e)}")
    else:
        # Test specific provider
        await test_provider(args.provider)

if __name__ == "__main__":
    asyncio.run(main()) 