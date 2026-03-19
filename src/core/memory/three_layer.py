# core/memory/three_layer.py
"""
Three-Layer Memory Manager

Implements Morpheus-style memory management with:
- L1 Identity Layer: Core rules, character definitions (permanent)
- L2 Runtime Layer: State changes, pending matters (temporary)
- L3 Log Layer: Chapter summaries (historical)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from .memory_item import MemoryItem, MemoryLayer, MemoryCategory
from .memory_store import MemoryStore, FileMemoryStore

logger = logging.getLogger(__name__)


# Token budget ratios (based on Morpheus)
BUDGET_RATIOS = {
    "identity_core": 0.15,      # L1: 15%
    "runtime_state": 0.10,      # L2: 10%
    "memory_compact": 0.15,     # L3 compact: 15%
    "previous_synopsis": 0.10,  # Previous synopsis: 10%
    "open_threads": 0.10,       # Open plot threads: 10%
    "previous_chapters": 0.35,  # Previous chapters: 35%
}


@dataclass
class ContextPack:
    """Context pack for chapter generation"""
    chapter: int
    identity_core: List[MemoryItem]
    runtime_state: List[MemoryItem]
    recent_logs: List[MemoryItem]
    open_threads: List[MemoryItem]
    token_budget: int
    estimated_tokens: int = 0


class ThreeLayerMemory:
    """Three-layer memory manager"""
    
    def __init__(self, store: Optional[MemoryStore] = None):
        """
        Initialize three-layer memory
        
        Args:
            store: Memory store (defaults to None, must be set before use)
        """
        self.store = store
        
        # Layer caches
        self._l1_cache: List[MemoryItem] = []  # Identity
        self._l2_cache: List[MemoryItem] = []  # Runtime
        self._l3_cache: List[MemoryItem] = []  # Log
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize and load existing memories"""
        if self._initialized:
            return
        
        if self.store is None:
            logger.warning("No store set, memory will be empty")
            self._initialized = True
            return
        
        # Load all items
        all_items = await self.store.list_all()
        
        # Sort into layer caches
        for item in all_items:
            if item.layer == MemoryLayer.L1_IDENTITY:
                self._l1_cache.append(item)
            elif item.layer == MemoryLayer.L2_RUNTIME:
                self._l2_cache.append(item)
            elif item.layer == MemoryLayer.L3_LOG:
                self._l3_cache.append(item)
        
        # Sort by importance
        self._l1_cache.sort(key=lambda x: x.importance, reverse=True)
        self._l2_cache.sort(key=lambda x: x.importance, reverse=True)
        self._l3_cache.sort(key=lambda x: x.source_chapter, reverse=True)
        
        self._initialized = True
        logger.info(
            f"Memory initialized: L1={len(self._l1_cache)}, "
            f"L2={len(self._l2_cache)}, L3={len(self._l3_cache)}"
        )
    
    async def add_memory(self, item: MemoryItem) -> None:
        """
        Add a memory item
        
        Args:
            item: Memory item to add
        """
        await self.initialize()
        
        # Save to store
        if self.store:
            await self.store.save(item)
        
        # Add to appropriate cache
        if item.layer == MemoryLayer.L1_IDENTITY:
            self._l1_cache.append(item)
            self._l1_cache.sort(key=lambda x: x.importance, reverse=True)
        elif item.layer == MemoryLayer.L2_RUNTIME:
            self._l2_cache.append(item)
            self._l2_cache.sort(key=lambda x: x.importance, reverse=True)
        elif item.layer == MemoryLayer.L3_LOG:
            self._l3_cache.append(item)
            self._l3_cache.sort(key=lambda x: x.source_chapter, reverse=True)
        
        logger.debug(f"Added memory: {item.id} to {item.layer.value}")
    
    async def add_identity(
        self,
        category: MemoryCategory,
        content: str,
        importance: int = 8,
        **kwargs
    ) -> MemoryItem:
        """Add L1 identity memory"""
        item = MemoryItem.create(
            layer=MemoryLayer.L1_IDENTITY,
            category=category,
            content=content,
            importance=importance,
            **kwargs
        )
        await self.add_memory(item)
        return item
    
    async def add_runtime(
        self,
        category: MemoryCategory,
        content: str,
        source_chapter: int,
        importance: int = 5,
        expires_chapter: Optional[int] = None,
        **kwargs
    ) -> MemoryItem:
        """Add L2 runtime memory"""
        item = MemoryItem.create(
            layer=MemoryLayer.L2_RUNTIME,
            category=category,
            content=content,
            importance=importance,
            source_chapter=source_chapter,
            expires_chapter=expires_chapter,
            **kwargs
        )
        await self.add_memory(item)
        return item
    
    async def add_log(
        self,
        category: MemoryCategory,
        content: str,
        source_chapter: int,
        importance: int = 3,
        **kwargs
    ) -> MemoryItem:
        """Add L3 log memory"""
        item = MemoryItem.create(
            layer=MemoryLayer.L3_LOG,
            category=category,
            content=content,
            importance=importance,
            source_chapter=source_chapter,
            **kwargs
        )
        await self.add_memory(item)
        return item
    
    async def get_identity(self) -> List[MemoryItem]:
        """Get L1 identity memories"""
        await self.initialize()
        return self._l1_cache.copy()
    
    async def get_runtime_state(self) -> List[MemoryItem]:
        """Get L2 runtime memories"""
        await self.initialize()
        return self._l2_cache.copy()
    
    async def get_recent_logs(self, limit: int = 10) -> List[MemoryItem]:
        """
        Get recent L3 log memories
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of recent log memories
        """
        await self.initialize()
        return self._l3_cache[:limit]
    
    async def get_logs_for_chapter(self, chapter: int) -> List[MemoryItem]:
        """Get L3 logs for a specific chapter"""
        await self.initialize()
        return [item for item in self._l3_cache if item.source_chapter == chapter]
    
    async def search(
        self,
        query: str,
        layer: Optional[MemoryLayer] = None
    ) -> List[MemoryItem]:
        """
        Search memories by content
        
        Args:
            query: Search query
            layer: Optional layer filter
            
        Returns:
            List of matching memories
        """
        await self.initialize()
        
        if self.store:
            return await self.store.search(query)
        
        # Fallback to in-memory search
        query_lower = query.lower()
        results = []
        
        caches = {
            MemoryLayer.L1_IDENTITY: self._l1_cache,
            MemoryLayer.L2_RUNTIME: self._l2_cache,
            MemoryLayer.L3_LOG: self._l3_cache,
        }
        
        for layer_key, cache in caches.items():
            if layer and layer != layer_key:
                continue
            
            for item in cache:
                if query_lower in item.content.lower():
                    results.append(item)
        
        results.sort(key=lambda x: x.importance, reverse=True)
        return results
    
    async def remove_expired(self, current_chapter: int) -> int:
        """
        Remove expired runtime memories
        
        Args:
            current_chapter: Current chapter number
            
        Returns:
            Number of removed items
        """
        await self.initialize()
        
        expired = [
            item for item in self._l2_cache
            if item.is_expired(current_chapter)
        ]
        
        for item in expired:
            self._l2_cache.remove(item)
            if self.store:
                await self.store.delete(item.id)
        
        if expired:
            logger.info(f"Removed {len(expired)} expired memories")
        
        return len(expired)
    
    async def build_context_pack(
        self,
        chapter: int,
        token_budget: int = 4000
    ) -> ContextPack:
        """
        Build context pack for chapter generation
        
        Args:
            chapter: Target chapter
            token_budget: Token budget for context
            
        Returns:
            ContextPack with relevant memories
        """
        await self.initialize()
        
        # Calculate budgets
        identity_budget = int(token_budget * BUDGET_RATIOS["identity_core"])
        runtime_budget = int(token_budget * BUDGET_RATIOS["runtime_state"])
        log_budget = int(token_budget * BUDGET_RATIOS["memory_compact"])
        
        # Get identity core (L1)
        identity_items = self._select_by_budget(self._l1_cache, identity_budget)
        
        # Get runtime state (L2) - filter expired
        runtime_items = [
            item for item in self._l2_cache
            if not item.is_expired(chapter)
        ]
        runtime_items = self._select_by_budget(runtime_items, runtime_budget)
        
        # Get recent logs (L3)
        log_items = self._select_by_budget(self._l3_cache, log_budget)
        
        # Get open threads (plot hooks from L2)
        open_threads = [
            item for item in self._l2_cache
            if item.category == MemoryCategory.PLOT
            and not item.is_expired(chapter)
        ]
        
        # Estimate tokens (rough: 4 chars per token for Chinese)
        def estimate_tokens(items: List[MemoryItem]) -> int:
            return sum(len(item.content) // 4 + 50 for item in items)
        
        estimated = (
            estimate_tokens(identity_items) +
            estimate_tokens(runtime_items) +
            estimate_tokens(log_items) +
            estimate_tokens(open_threads)
        )
        
        return ContextPack(
            chapter=chapter,
            identity_core=identity_items,
            runtime_state=runtime_items,
            recent_logs=log_items,
            open_threads=open_threads,
            token_budget=token_budget,
            estimated_tokens=estimated,
        )
    
    def _select_by_budget(
        self,
        items: List[MemoryItem],
        token_budget: int
    ) -> List[MemoryItem]:
        """Select items within token budget"""
        selected = []
        current_tokens = 0
        
        for item in items:
            # Rough token estimate
            item_tokens = len(item.content) // 4 + 50
            
            if current_tokens + item_tokens <= token_budget:
                selected.append(item)
                current_tokens += item_tokens
            else:
                break
        
        return selected
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get memory summary"""
        await self.initialize()
        
        return {
            "l1_identity": {
                "count": len(self._l1_cache),
                "categories": self._count_categories(self._l1_cache),
            },
            "l2_runtime": {
                "count": len(self._l2_cache),
                "categories": self._count_categories(self._l2_cache),
            },
            "l3_log": {
                "count": len(self._l3_cache),
                "categories": self._count_categories(self._l3_cache),
            },
        }
    
    def _count_categories(self, items: List[MemoryItem]) -> Dict[str, int]:
        """Count items by category"""
        counts = {}
        for item in items:
            cat = item.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    async def clear_layer(self, layer: MemoryLayer) -> int:
        """Clear all memories in a layer"""
        await self.initialize()
        
        if layer == MemoryLayer.L1_IDENTITY:
            count = len(self._l1_cache)
            self._l1_cache.clear()
        elif layer == MemoryLayer.L2_RUNTIME:
            count = len(self._l2_cache)
            self._l2_cache.clear()
        else:
            count = len(self._l3_cache)
            self._l3_cache.clear()
        
        if self.store:
            items = await self.store.query(layer=layer)
            for item in items:
                await self.store.delete(item.id)
        
        logger.info(f"Cleared {count} memories from {layer.value}")
        return count