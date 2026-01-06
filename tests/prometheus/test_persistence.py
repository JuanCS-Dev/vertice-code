"""
Test Prometheus Persistence Integration.

Verifies Phase 4 (Persistent State & Evolution).
"""

import asyncio
import os
import shutil
import pytest
import aiosqlite
from prometheus.core.persistence import PersistenceLayer
from prometheus.core.orchestrator import PrometheusOrchestrator

TEST_DB_PATH = ".prometheus/test_persistence.db"

@pytest.fixture
async def persistence():
    """Setup and teardown persistence layer."""
    # Cleanup before
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    layer = PersistenceLayer(db_path=TEST_DB_PATH)
    await layer.initialize()
    yield layer
    
    # Cleanup after
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.mark.asyncio
async def test_save_and_load_state(persistence):
    """Test saving and loading agent state."""
    state = {"key": "value", "number": 42}
    await persistence.save_state("test_agent", state)
    
    loaded = await persistence.load_state("test_agent")
    assert loaded == state

@pytest.mark.asyncio
async def test_store_and_retrieve_memory(persistence):
    """Test memory storage."""
    await persistence.store_memory(
        memory_id="m1",
        type="semantic",
        content="Python is great",
        metadata={"tags": ["coding"]},
        importance=0.9
    )
    
    memories = await persistence.retrieve_memories("semantic")
    assert len(memories) == 1
    assert memories[0]["content"] == "Python is great"
    assert memories[0]["metadata"]["tags"] == ["coding"]

@pytest.mark.asyncio
async def test_orchestrator_auto_save():
    """Test that orchestrator auto-saves state."""
    # Setup orchestrator with test DB
    from prometheus.core.persistence import persistence as orchestrator_persistence
    
    original_path = orchestrator_persistence.db_path
    orchestrator_persistence.db_path = TEST_DB_PATH
    orchestrator_persistence._initialized = False # Force re-init
    
    orchestrator = PrometheusOrchestrator(agent_name="TestAutoSave")
    
    # Execute something simple
    # We mock _execute_task_with_context to avoid LLM calls
    from unittest.mock import AsyncMock
    orchestrator._execute_task_with_context = AsyncMock(return_value="Done")
    
    try:
        async for _ in orchestrator.execute("Test Task", fast_mode=True):
            pass
            
        # Verify state was saved
        saved = await orchestrator_persistence.load_state("TestAutoSave")
        assert saved is not None
        assert "agent_name" in saved
        assert saved["agent_name"] == "TestAutoSave"
        
    finally:
        # Cleanup
        orchestrator_persistence.db_path = original_path
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
