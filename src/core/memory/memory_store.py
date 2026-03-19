# core/memory/memory_store.py
"""
Memory Store - Base class and file-based implementation
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import asyncio
import logging
from datetime import datetime

from .memory_item import MemoryItem, MemoryLayer, MemoryCategory

logger = logging.getLogger(__name__)


class MemoryStore(ABC):
    """Abstract memory store"""
    
    @abstractmethod
    async def save(self, item: MemoryItem) -> None:
        """Save a memory item"""
        pass
    
    @abstractmethod
    async def load(self, item_id: str) -> Optional[MemoryItem]:
        """Load a memory item by ID"""
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[MemoryItem]:
        """List all memory items"""
        pass
    
    @abstractmethod
    async def query(
        self,
        layer: Optional[MemoryLayer] = None,
        category: Optional[MemoryCategory] = None,
        source_chapter: Optional[int] = None,
        min_importance: Optional[int] = None,
    ) -> List[MemoryItem]:
        """Query memory items"""
        pass
    
    @abstractmethod
    async def search(self, query: str) -> List[MemoryItem]:
        """Search memory items by content"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory items"""
        pass


class FileMemoryStore(MemoryStore):
    """File-based memory store"""
    
    def __init__(self, storage_path: str):
        """
        Initialize file-based memory store
        
        Args:
            storage_path: Directory for storing memory files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._lock = asyncio.Lock()
        self._cache: Dict[str, MemoryItem] = {}
        self._loaded = False
        
        logger.info(f"FileMemoryStore initialized: {storage_path}")
    
    def _get_layer_file(self, layer: MemoryLayer) -> Path:
        """Get file path for a layer"""
        return self.storage_path / f"{layer.value}_memory.json"
    
    async def _load_all(self) -> None:
        """Load all memory items from files"""
        if self._loaded:
            return
        
        async with self._lock:
            if self._loaded:
                return
            
            for layer in MemoryLayer:
                file_path = self._get_layer_file(layer)
                if file_path.exists():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        for item_data in data.get("items", []):
                            item = MemoryItem.from_dict(item_data)
                            self._cache[item.id] = item
                    except Exception as e:
                        logger.error(f"Failed to load {file_path}: {e}")
            
            self._loaded = True
            logger.debug(f"Loaded {len(self._cache)} memory items")
    
    async def _save_layer(self, layer: MemoryLayer) -> None:
        """Save a layer to file"""
        items = [
            item.to_dict() 
            for item in self._cache.values() 
            if item.layer == layer
        ]
        
        file_path = self._get_layer_file(layer)
        data = {
            "layer": layer.value,
            "updated_at": datetime.now().isoformat(),
            "items": items,
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"Saved {len(items)} items to {file_path}")
    
    async def save(self, item: MemoryItem) -> None:
        """Save a memory item"""
        await self._load_all()
        
        async with self._lock:
            self._cache[item.id] = item
            await self._save_layer(item.layer)
        
        logger.info(f"Saved memory: {item.id}")
    
    async def load(self, item_id: str) -> Optional[MemoryItem]:
        """Load a memory item by ID"""
        await self._load_all()
        return self._cache.get(item_id)
    
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item"""
        await self._load_all()
        
        async with self._lock:
            item = self._cache.get(item_id)
            if item is None:
                return False
            
            del self._cache[item_id]
            await self._save_layer(item.layer)
        
        logger.info(f"Deleted memory: {item_id}")
        return True
    
    async def list_all(self) -> List[MemoryItem]:
        """List all memory items"""
        await self._load_all()
        return list(self._cache.values())
    
    async def query(
        self,
        layer: Optional[MemoryLayer] = None,
        category: Optional[MemoryCategory] = None,
        source_chapter: Optional[int] = None,
        min_importance: Optional[int] = None,
    ) -> List[MemoryItem]:
        """Query memory items"""
        await self._load_all()
        
        results = []
        for item in self._cache.values():
            if layer and item.layer != layer:
                continue
            if category and item.category != category:
                continue
            if source_chapter is not None and item.source_chapter != source_chapter:
                continue
            if min_importance is not None and item.importance < min_importance:
                continue
            results.append(item)
        
        return results
    
    async def search(self, query: str) -> List[MemoryItem]:
        """Search memory items by content"""
        await self._load_all()
        
        query_lower = query.lower()
        results = []
        
        for item in self._cache.values():
            if query_lower in item.content.lower():
                results.append(item)
            elif any(query_lower in tag.lower() for tag in item.tags):
                results.append(item)
        
        # Sort by importance
        results.sort(key=lambda x: x.importance, reverse=True)
        return results
    
    async def clear(self) -> None:
        """Clear all memory items"""
        async with self._lock:
            self._cache.clear()
            self._loaded = True
            
            for layer in MemoryLayer:
                file_path = self._get_layer_file(layer)
                if file_path.exists():
                    file_path.unlink()
            
            logger.info("All memory items cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        await self._load_all()
        
        stats = {
            "total": len(self._cache),
            "by_layer": {},
            "by_category": {},
        }
        
        for layer in MemoryLayer:
            stats["by_layer"][layer.value] = sum(
                1 for item in self._cache.values() if item.layer == layer
            )
        
        for category in MemoryCategory:
            stats["by_category"][category.value] = sum(
                1 for item in self._cache.values() if item.category == category
            )
        
        return stats