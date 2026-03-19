# tests/test_memory.py
"""
Tests for Three-Layer Memory System
"""

import pytest
import tempfile
from datetime import datetime
from src.core.memory import (
    MemoryItem,
    MemoryLayer,
    MemoryCategory,
    MemoryStore,
    FileMemoryStore,
    ThreeLayerMemory,
)


class TestMemoryItem:
    """Test MemoryItem dataclass"""
    
    def test_create_memory_item(self):
        """Test memory item creation"""
        item = MemoryItem.create(
            layer=MemoryLayer.L1_IDENTITY,
            category=MemoryCategory.WORLD,
            content="World rule: Magic costs mana",
            importance=10,
            source_chapter=0
        )
        
        assert item.layer == MemoryLayer.L1_IDENTITY
        assert item.category == MemoryCategory.WORLD
        assert item.content == "World rule: Magic costs mana"
        assert item.importance == 10
        assert item.id.startswith("mem_")
    
    def test_memory_item_to_dict(self):
        """Test serialization"""
        item = MemoryItem.create(
            layer=MemoryLayer.L2_RUNTIME,
            category=MemoryCategory.CHARACTER,
            content="Hero is wounded",
            importance=7
        )
        
        d = item.to_dict()
        assert d["layer"] == "L2"
        assert d["category"] == "character"
        assert d["content"] == "Hero is wounded"
    
    def test_memory_item_from_dict(self):
        """Test deserialization"""
        data = {
            "id": "mem_test",
            "layer": "L1",
            "category": "world",
            "content": "Test content",
            "importance": 5,
            "source_chapter": 1,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "expires_chapter": None,
            "metadata": {},
            "tags": []
        }
        
        item = MemoryItem.from_dict(data)
        assert item.id == "mem_test"
        assert item.layer == MemoryLayer.L1_IDENTITY
        assert item.importance == 5
    
    def test_memory_expiration(self):
        """Test memory expiration check"""
        item = MemoryItem.create(
            layer=MemoryLayer.L2_RUNTIME,
            category=MemoryCategory.EVENT,
            content="Temporary event",
            expires_chapter=5
        )
        
        assert item.is_expired(4) is False
        assert item.is_expired(5) is False
        assert item.is_expired(6) is True
    
    def test_memory_update(self):
        """Test memory update"""
        item = MemoryItem.create(
            layer=MemoryLayer.L1_IDENTITY,
            category=MemoryCategory.WORLD,
            content="Original content",
            importance=5
        )
        
        import time
        time.sleep(0.01)  # Ensure timestamp difference
        
        item.update(content="Updated content", importance=8)
        
        assert item.content == "Updated content"
        assert item.importance == 8
        # updated_at should be >= created_at (may be same if very fast)
        assert item.updated_at >= item.created_at


class TestMemoryLayer:
    """Test memory layer enum"""
    
    def test_layer_values(self):
        """Test layer enum values"""
        assert MemoryLayer.L1_IDENTITY.value == "L1"
        assert MemoryLayer.L2_RUNTIME.value == "L2"
        assert MemoryLayer.L3_LOG.value == "L3"


class TestMemoryCategory:
    """Test memory category enum"""
    
    def test_category_values(self):
        """Test category enum values"""
        assert MemoryCategory.WORLD.value == "world"
        assert MemoryCategory.CHARACTER.value == "character"
        assert MemoryCategory.PLOT.value == "plot"


class TestFileMemoryStore:
    """Test FileMemoryStore"""
    
    @pytest.mark.asyncio
    async def test_save_and_load(self):
        """Test save and load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            
            item = MemoryItem.create(
                layer=MemoryLayer.L1_IDENTITY,
                category=MemoryCategory.WORLD,
                content="Test memory",
                importance=8
            )
            
            await store.save(item)
            
            loaded = await store.load(item.id)
            assert loaded is not None
            assert loaded.content == "Test memory"
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            
            item = MemoryItem.create(
                layer=MemoryLayer.L1_IDENTITY,
                category=MemoryCategory.WORLD,
                content="To be deleted"
            )
            
            await store.save(item)
            success = await store.delete(item.id)
            
            assert success is True
            loaded = await store.load(item.id)
            assert loaded is None
    
    @pytest.mark.asyncio
    async def test_query(self):
        """Test query"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            
            # Add items
            item1 = MemoryItem.create(
                layer=MemoryLayer.L1_IDENTITY,
                category=MemoryCategory.WORLD,
                content="World rule",
                importance=10
            )
            item2 = MemoryItem.create(
                layer=MemoryLayer.L2_RUNTIME,
                category=MemoryCategory.CHARACTER,
                content="Character state",
                importance=5
            )
            item3 = MemoryItem.create(
                layer=MemoryLayer.L1_IDENTITY,
                category=MemoryCategory.CHARACTER,
                content="Character definition",
                importance=8
            )
            
            await store.save(item1)
            await store.save(item2)
            await store.save(item3)
            
            # Query by layer
            l1_items = await store.query(layer=MemoryLayer.L1_IDENTITY)
            assert len(l1_items) == 2
            
            # Query by category
            char_items = await store.query(category=MemoryCategory.CHARACTER)
            assert len(char_items) == 2
            
            # Query by importance
            important = await store.query(min_importance=8)
            assert len(important) == 2
    
    @pytest.mark.asyncio
    async def test_search(self):
        """Test search"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            
            item1 = MemoryItem.create(
                layer=MemoryLayer.L1_IDENTITY,
                category=MemoryCategory.WORLD,
                content="Magic system uses mana"
            )
            item2 = MemoryItem.create(
                layer=MemoryLayer.L1_IDENTITY,
                category=MemoryCategory.WORLD,
                content="Combat is turn-based"
            )
            
            await store.save(item1)
            await store.save(item2)
            
            results = await store.search("mana")
            assert len(results) == 1
            assert "mana" in results[0].content
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            
            await store.save(MemoryItem.create(
                layer=MemoryLayer.L1_IDENTITY,
                category=MemoryCategory.WORLD,
                content="Rule 1"
            ))
            await store.save(MemoryItem.create(
                layer=MemoryLayer.L2_RUNTIME,
                category=MemoryCategory.CHARACTER,
                content="State 1"
            ))
            
            stats = await store.get_stats()
            assert stats["total"] == 2
            assert stats["by_layer"]["L1"] == 1
            assert stats["by_layer"]["L2"] == 1


class TestThreeLayerMemory:
    """Test ThreeLayerMemory"""
    
    @pytest.mark.asyncio
    async def test_initialize_empty(self):
        """Test initialization with no store"""
        memory = ThreeLayerMemory(store=None)
        await memory.initialize()
        
        identity = await memory.get_identity()
        assert identity == []
    
    @pytest.mark.asyncio
    async def test_add_memory(self):
        """Test adding memories to different layers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            memory = ThreeLayerMemory(store=store)
            
            # Add to each layer
            await memory.add_identity(
                category=MemoryCategory.WORLD,
                content="World rule 1"
            )
            await memory.add_runtime(
                category=MemoryCategory.EVENT,
                content="Event started",
                source_chapter=1
            )
            await memory.add_log(
                category=MemoryCategory.PLOT,
                content="Chapter 1 summary",
                source_chapter=1
            )
            
            # Check each layer
            identity = await memory.get_identity()
            assert len(identity) == 1
            
            runtime = await memory.get_runtime_state()
            assert len(runtime) == 1
            
            logs = await memory.get_recent_logs()
            assert len(logs) == 1
    
    @pytest.mark.asyncio
    async def test_search(self):
        """Test search across layers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            memory = ThreeLayerMemory(store=store)
            
            await memory.add_identity(
                category=MemoryCategory.CHARACTER,
                content="Hero is brave"
            )
            await memory.add_runtime(
                category=MemoryCategory.EVENT,
                content="Hero saves village",
                source_chapter=1
            )
            
            results = await memory.search("Hero")
            assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_remove_expired(self):
        """Test removing expired memories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            memory = ThreeLayerMemory(store=store)
            
            # Add expiring memory
            await memory.add_runtime(
                category=MemoryCategory.EVENT,
                content="Temporary event",
                source_chapter=1,
                expires_chapter=3
            )
            await memory.add_runtime(
                category=MemoryCategory.EVENT,
                content="Permanent event",
                source_chapter=1
            )
            
            # Check before expiration
            runtime = await memory.get_runtime_state()
            assert len(runtime) == 2
            
            # Remove expired
            removed = await memory.remove_expired(4)
            assert removed == 1
            
            # Check after
            runtime = await memory.get_runtime_state()
            assert len(runtime) == 1
    
    @pytest.mark.asyncio
    async def test_build_context_pack(self):
        """Test context pack building"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            memory = ThreeLayerMemory(store=store)
            
            # Add memories
            await memory.add_identity(
                category=MemoryCategory.WORLD,
                content="World rule: " + "x" * 100,
                importance=10
            )
            await memory.add_runtime(
                category=MemoryCategory.CHARACTER,
                content="Character state: " + "y" * 50,
                source_chapter=1
            )
            await memory.add_log(
                category=MemoryCategory.PLOT,
                content="Chapter summary: " + "z" * 80,
                source_chapter=1
            )
            
            # Build context pack
            pack = await memory.build_context_pack(chapter=2, token_budget=1000)
            
            assert pack.chapter == 2
            assert len(pack.identity_core) >= 1
            assert len(pack.runtime_state) >= 1
            assert pack.estimated_tokens > 0
    
    @pytest.mark.asyncio
    async def test_get_summary(self):
        """Test memory summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            memory = ThreeLayerMemory(store=store)
            
            await memory.add_identity(
                category=MemoryCategory.WORLD,
                content="Rule"
            )
            await memory.add_runtime(
                category=MemoryCategory.CHARACTER,
                content="State",
                source_chapter=1
            )
            
            summary = await memory.get_summary()
            
            assert summary["l1_identity"]["count"] == 1
            assert summary["l2_runtime"]["count"] == 1
            assert "world" in summary["l1_identity"]["categories"]
    
    @pytest.mark.asyncio
    async def test_clear_layer(self):
        """Test clearing specific layer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(tmpdir)
            memory = ThreeLayerMemory(store=store)
            
            await memory.add_identity(
                category=MemoryCategory.WORLD,
                content="Rule"
            )
            await memory.add_runtime(
                category=MemoryCategory.EVENT,
                content="Event",
                source_chapter=1
            )
            
            # Clear L2
            count = await memory.clear_layer(MemoryLayer.L2_RUNTIME)
            assert count == 1
            
            # L1 should still exist
            identity = await memory.get_identity()
            assert len(identity) == 1
            
            # L2 should be empty
            runtime = await memory.get_runtime_state()
            assert len(runtime) == 0