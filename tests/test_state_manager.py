# tests/test_state_manager.py
"""
Tests for State Manager
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.core.state_manager import (
    StateManager,
    StateSnapshot,
    WorldState,
    CharacterState,
    PlotState,
)


class TestStateSnapshot:
    """Test StateSnapshot dataclass"""
    
    def test_create_snapshot(self):
        """Test snapshot creation"""
        data = {"test": "data", "nested": {"key": "value"}}
        snapshot = StateSnapshot.create(chapter=1, data=data)
        
        assert snapshot.chapter == 1
        assert snapshot.data == data
        assert snapshot.snapshot_id.startswith("snapshot_1_")
        assert snapshot.timestamp
    
    def test_snapshot_to_dict(self):
        """Test snapshot serialization"""
        snapshot = StateSnapshot.create(chapter=5, data={"hp": 100})
        d = snapshot.to_dict()
        
        assert d["chapter"] == 5
        assert d["data"]["hp"] == 100
        assert "snapshot_id" in d
        assert "timestamp" in d
    
    def test_snapshot_from_dict(self):
        """Test snapshot deserialization"""
        data = {
            "snapshot_id": "test_id",
            "timestamp": "2024-01-01T00:00:00",
            "chapter": 3,
            "data": {"location": "town"}
        }
        snapshot = StateSnapshot.from_dict(data)
        
        assert snapshot.snapshot_id == "test_id"
        assert snapshot.chapter == 3
        assert snapshot.data["location"] == "town"


class TestStateManager:
    """Test StateManager"""
    
    @pytest.mark.asyncio
    async def test_save_and_load_snapshot(self):
        """Test saving and loading snapshots"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            # Save snapshot
            data = {
                "world_state": {"current_time": "2024-01-01"},
                "characters": {"hero": {"hp": 100}},
            }
            snapshot = await manager.save_snapshot(1, data)
            
            assert snapshot.chapter == 1
            assert snapshot.data == data
            
            # Load snapshot
            loaded = await manager.load_snapshot(1)
            assert loaded is not None
            assert loaded.data == data
    
    @pytest.mark.asyncio
    async def test_list_snapshots(self):
        """Test listing snapshots"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            # Save multiple snapshots
            await manager.save_snapshot(1, {"chapter": 1})
            await manager.save_snapshot(2, {"chapter": 2})
            await manager.save_snapshot(3, {"chapter": 3})
            
            # List snapshots
            snapshots = await manager.list_snapshots()
            assert len(snapshots) == 3
            assert snapshots[0].chapter == 1
            assert snapshots[2].chapter == 3
    
    @pytest.mark.asyncio
    async def test_rollback(self):
        """Test rollback functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            # Save snapshots
            await manager.save_snapshot(1, {"chapter": 1})
            await manager.save_snapshot(2, {"chapter": 2})
            await manager.save_snapshot(3, {"chapter": 3})
            
            # Rollback to chapter 2
            success = await manager.rollback(2)
            assert success is True
            
            # Check state
            state = await manager.get_current_state()
            assert state["chapter"] == 2
            
            # Verify chapter 3 is deleted
            snapshots = await manager.list_snapshots()
            assert len(snapshots) == 2
            assert all(s.chapter <= 2 for s in snapshots)
    
    @pytest.mark.asyncio
    async def test_get_current_state(self):
        """Test getting current state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            # Initially empty
            state = await manager.get_current_state()
            assert state == {}
            
            # After save
            await manager.save_snapshot(5, {"location": "forest"})
            state = await manager.get_current_state()
            assert state["location"] == "forest"
    
    @pytest.mark.asyncio
    async def test_update_state(self):
        """Test updating state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            await manager.save_snapshot(1, {"hp": 100})
            await manager.update_state({"mp": 50})
            
            state = await manager.get_current_state()
            assert state["hp"] == 100
            assert state["mp"] == 50
    
    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Test clearing all snapshots"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            await manager.save_snapshot(1, {"a": 1})
            await manager.save_snapshot(2, {"b": 2})
            
            await manager.clear_all()
            
            snapshots = await manager.list_snapshots()
            assert len(snapshots) == 0
            
            state = await manager.get_current_state()
            assert state == {}
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_snapshot(self):
        """Test loading nonexistent snapshot"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            snapshot = await manager.load_snapshot(999)
            assert snapshot is None
    
    @pytest.mark.asyncio
    async def test_rollback_nonexistent(self):
        """Test rollback to nonexistent chapter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)
            
            success = await manager.rollback(999)
            assert success is False


class TestStateStructures:
    """Test state data structures"""
    
    def test_world_state(self):
        """Test WorldState"""
        state = WorldState(
            current_time="2024-01-01T10:00:00",
            weather="sunny",
            active_events=["festival"]
        )
        assert state.current_time == "2024-01-01T10:00:00"
        assert state.weather == "sunny"
        assert "festival" in state.active_events
    
    def test_character_state(self):
        """Test CharacterState"""
        state = CharacterState(
            location="town_square",
            hp=80,
            status=["poisoned"]
        )
        assert state.location == "town_square"
        assert state.hp == 80
        assert "poisoned" in state.status
    
    def test_plot_state(self):
        """Test PlotState"""
        state = PlotState(
            active_hooks=["hook_001", "hook_002"],
            resolved_hooks=["hook_000"],
            current_arc="arc_1"
        )
        assert len(state.active_hooks) == 2
        assert "hook_000" in state.resolved_hooks
        assert state.current_arc == "arc_1"