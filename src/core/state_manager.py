# core/state_manager.py
"""
State Manager Module - Snapshot and rollback support

Features:
- JSON-based snapshot storage
- Async file operations with locking
- Chapter-based state management
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    """State snapshot"""
    snapshot_id: str
    timestamp: str
    chapter: int
    data: Dict[str, Any]
    
    @classmethod
    def create(cls, chapter: int, data: Dict[str, Any]) -> "StateSnapshot":
        """Create a new snapshot"""
        timestamp = datetime.now().isoformat()
        snapshot_id = f"snapshot_{chapter}_{timestamp.replace(':', '-').replace('.', '-')}"
        return cls(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            chapter=chapter,
            data=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class WorldState:
    """World state structure"""
    current_time: str = ""
    weather: str = "unknown"
    active_events: List[str] = field(default_factory=list)


@dataclass
class CharacterState:
    """Character state"""
    location: str = ""
    hp: int = 100
    status: List[str] = field(default_factory=list)


@dataclass
class PlotState:
    """Plot state"""
    active_hooks: List[str] = field(default_factory=list)
    resolved_hooks: List[str] = field(default_factory=list)
    current_arc: str = ""


class StateManager:
    """State manager with snapshot and rollback"""
    
    def __init__(self, storage_path: str):
        """
        Initialize state manager
        
        Args:
            storage_path: Directory for storing state files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # File lock for concurrent access
        self._lock = asyncio.Lock()
        
        # Current state cache
        self._current_state: Dict[str, Any] = {}
        self._current_chapter: int = 0
        
        logger.info(f"StateManager initialized: {storage_path}")
    
    def _get_snapshot_path(self, chapter: int) -> Path:
        """Get snapshot file path for a chapter"""
        return self.storage_path / f"chapter_{chapter:04d}.json"
    
    def _get_index_path(self) -> Path:
        """Get index file path"""
        return self.storage_path / "index.json"
    
    async def save_snapshot(
        self,
        chapter: int,
        data: Dict[str, Any]
    ) -> StateSnapshot:
        """
        Save state snapshot
        
        Args:
            chapter: Chapter number
            data: State data to save
            
        Returns:
            Created snapshot
        """
        async with self._lock:
            snapshot = StateSnapshot.create(chapter, data)
            snapshot_path = self._get_snapshot_path(chapter)
            
            # Write snapshot
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Update index
            await self._update_index(chapter, snapshot)
            
            # Update cache
            self._current_state = data
            self._current_chapter = chapter
            
            logger.info(f"Snapshot saved: chapter={chapter}, id={snapshot.snapshot_id}")
            return snapshot
    
    async def load_snapshot(self, chapter: int) -> Optional[StateSnapshot]:
        """
        Load snapshot for a chapter
        
        Args:
            chapter: Chapter number
            
        Returns:
            Snapshot or None if not found
        """
        async with self._lock:
            snapshot_path = self._get_snapshot_path(chapter)
            
            if not snapshot_path.exists():
                logger.debug(f"Snapshot not found: chapter={chapter}")
                return None
            
            with open(snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            snapshot = StateSnapshot.from_dict(data)
            logger.debug(f"Snapshot loaded: chapter={chapter}")
            return snapshot
    
    async def list_snapshots(self) -> List[StateSnapshot]:
        """
        List all snapshots
        
        Returns:
            List of snapshots sorted by chapter
        """
        async with self._lock:
            index_path = self._get_index_path()
            
            if not index_path.exists():
                return []
            
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            snapshots = []
            for item in index_data.get("snapshots", []):
                snapshots.append(StateSnapshot.from_dict(item))
            
            return sorted(snapshots, key=lambda s: s.chapter)
    
    async def rollback(self, chapter: int) -> bool:
        """
        Rollback to a specific chapter
        
        Args:
            chapter: Target chapter
            
        Returns:
            True if rollback successful
        """
        snapshot = await self.load_snapshot(chapter)
        
        if snapshot is None:
            logger.warning(f"Rollback failed: chapter={chapter} not found")
            return False
        
        # Update current state
        self._current_state = snapshot.data
        self._current_chapter = chapter
        
        # Delete later snapshots
        await self._delete_snapshots_after(chapter)
        
        logger.info(f"Rollback complete: chapter={chapter}")
        return True
    
    async def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state
        
        Returns:
            Current state dictionary
        """
        if not self._current_state:
            # Try to load latest snapshot
            snapshots = await self.list_snapshots()
            if snapshots:
                latest = snapshots[-1]
                loaded = await self.load_snapshot(latest.chapter)
                if loaded:
                    self._current_state = loaded.data
                    self._current_chapter = loaded.chapter
        
        return self._current_state.copy()
    
    async def get_current_chapter(self) -> int:
        """Get current chapter number"""
        return self._current_chapter
    
    async def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update current state (in-memory only, call save_snapshot to persist)
        
        Args:
            updates: State updates
        """
        self._current_state.update(updates)
    
    async def _update_index(self, chapter: int, snapshot: StateSnapshot) -> None:
        """Update snapshot index"""
        index_path = self._get_index_path()
        
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        else:
            index_data = {"snapshots": []}
        
        # Remove existing entry for this chapter
        index_data["snapshots"] = [
            s for s in index_data["snapshots"]
            if s.get("chapter") != chapter
        ]
        
        # Add new entry
        index_data["snapshots"].append(snapshot.to_dict())
        
        # Sort by chapter
        index_data["snapshots"].sort(key=lambda s: s.get("chapter", 0))
        
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    async def _delete_snapshots_after(self, chapter: int) -> None:
        """Delete all snapshots after a chapter"""
        snapshots = await self.list_snapshots()
        
        for snapshot in snapshots:
            if snapshot.chapter > chapter:
                snapshot_path = self._get_snapshot_path(snapshot.chapter)
                if snapshot_path.exists():
                    snapshot_path.unlink()
                    logger.debug(f"Deleted snapshot: chapter={snapshot.chapter}")
        
        # Update index
        index_path = self._get_index_path()
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        
        index_data["snapshots"] = [
            s for s in index_data["snapshots"]
            if s.get("chapter", 0) <= chapter
        ]
        
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    async def clear_all(self) -> None:
        """Clear all snapshots"""
        async with self._lock:
            for file in self.storage_path.glob("*.json"):
                file.unlink()
            
            self._current_state = {}
            self._current_chapter = 0
            
            logger.info("All snapshots cleared")