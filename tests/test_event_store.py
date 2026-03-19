# tests/test_event_store.py
"""事件存储测试"""

import pytest
import asyncio
import tempfile
import os
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.events import Event, EventType
from core.event_store import EventStore


def get_temp_db_path():
    """获取临时数据库路径"""
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = f.name
    f.close()
    return path


@pytest.mark.asyncio
async def test_event_store_initialize():
    """测试存储初始化"""
    db_path = get_temp_db_path()
    try:
        store = EventStore(db_path)
        await store.initialize()
        assert store._db is not None
        await store.close()
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_event_store_append():
    """测试追加事件"""
    db_path = get_temp_db_path()
    try:
        store = EventStore(db_path)
        await store.initialize()
        
        event = Event(
            event_type=EventType.SIMULATION_STARTED,
            simulation_time=0.0,
            data={"simulation_id": "test", "time_scale": 1.0}
        )
        await store.append(event)
        
        count = await store.get_event_count()
        assert count == 1
        
        await store.close()
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_event_store_append_batch():
    """测试批量追加事件"""
    db_path = get_temp_db_path()
    try:
        store = EventStore(db_path)
        await store.initialize()
        
        events = [
            Event(
                event_type=EventType.SIMULATION_STARTED,
                simulation_time=float(i),
                data={"index": i}
            )
            for i in range(5)
        ]
        await store.append_batch(events)
        
        count = await store.get_event_count()
        assert count == 5
        
        await store.close()
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_event_store_get_events():
    """测试获取事件"""
    db_path = get_temp_db_path()
    try:
        store = EventStore(db_path)
        await store.initialize()
        
        # 添加一些事件
        for i in range(3):
            await store.append(Event(
                event_type=EventType.TIME_SCALED,
                simulation_time=float(i * 10),
                data={"scale": i}
            ))
        
        # 获取事件
        events = await store.get_events(from_time=5.0)
        assert len(events) == 2  # time >= 5.0 的有 2 个
        
        await store.close()
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_event_store_get_latest_time():
    """测试获取最新时间"""
    db_path = get_temp_db_path()
    try:
        store = EventStore(db_path)
        await store.initialize()
        
        await store.append(Event(
            event_type=EventType.SIMULATION_STARTED,
            simulation_time=100.0,
            data={}
        ))
        
        latest = await store.get_latest_time()
        assert latest == 100.0
        
        await store.close()
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_event_store_clear():
    """测试清空存储"""
    db_path = get_temp_db_path()
    try:
        store = EventStore(db_path)
        await store.initialize()
        
        await store.append(Event(
            event_type=EventType.SIMULATION_STARTED,
            simulation_time=0.0,
            data={}
        ))
        
        await store.clear()
        count = await store.get_event_count()
        assert count == 0
        
        await store.close()
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.mark.asyncio
async def test_event_store_stream_events():
    """测试流式获取事件"""
    db_path = get_temp_db_path()
    try:
        store = EventStore(db_path)
        await store.initialize()
        
        for i in range(3):
            await store.append(Event(
                event_type=EventType.MARKER_CREATED,
                simulation_time=float(i),
                data={"label": f"marker-{i}"}
            ))
        
        events = []
        async for event in store.stream_events():
            events.append(event)
        
        assert len(events) == 3
        
        await store.close()
    finally:
        try:
            os.unlink(db_path)
        except:
            pass