"""Test brain clients and orchestrator functionality."""
import asyncio
import pytest
from tova.brains import MixtralClient, PhiClient
from tova.core import TovaOrchestrator


@pytest.mark.asyncio
async def test_brain_clients():
    """Test basic brain client functionality."""
    mixtral = MixtralClient("http://localhost:8000")
    phi = PhiClient("http://localhost:8001")
    
    # Test health checks (will fail if servers not running)
    mixtral_health = await mixtral.health_check()
    phi_health = await phi.health_check()
    
    # Health endpoint for llama.cpp old version is /v1/models
    print(f"Mixtral health (/v1/models): {mixtral_health}")
    print(f"Phi health (/v1/models): {phi_health}")
    
    await mixtral.close()
    await phi.close()


@pytest.mark.asyncio
async def test_orchestrator():
    """Test orchestrator initialization."""
    orchestrator = TovaOrchestrator()
    
    # Test initialization (will fail if brains not running)
    success = await orchestrator.initialize()
    print(f"Orchestrator initialization: {success}")
    
    if success:
        await orchestrator.shutdown()


if __name__ == "__main__":
    print("Testing brain clients...")
    asyncio.run(test_brain_clients())
    
    print("\nTesting orchestrator...")
    asyncio.run(test_orchestrator()) 