# tests/test_events.py
"""事件模型测试"""

import pytest
from src.core.events import Event, EventType, EventValidator, EventValidationError


def test_event_creation():
    """测试事件创建"""
    event = Event(
        event_type=EventType.SIMULATION_STARTED,
        simulation_time=0.0,
        data={}
    )
    assert event.event_type == EventType.SIMULATION_STARTED
    assert event.simulation_time == 0.0


def test_event_with_data():
    """测试带数据的事件"""
    event = Event(
        event_type=EventType.ENTITY_CREATED,
        simulation_time=1.0,
        data={"entity_id": "test-001", "type": "character", "position": [0, 0]}
    )
    assert event.data["entity_id"] == "test-001"
    assert event.event_id is not None  # 自动生成 UUID


def test_event_to_dict():
    """测试事件序列化"""
    event = Event(
        event_type=EventType.SIMULATION_STARTED,
        simulation_time=0.0,
        data={"simulation_id": "test-sim", "time_scale": 1.0}
    )
    d = event.to_dict()
    assert d["event_type"] == "simulation.started"
    assert "event_id" in d
    assert "created_at" in d


def test_event_from_dict():
    """测试事件反序列化"""
    data = {
        "event_id": "00000000-0000-0000-0000-000000000001",
        "simulation_time": 1.0,
        "event_type": "simulation.started",
        "data": {"simulation_id": "test"},
        "metadata": {},
        "causation_id": None,
        "correlation_id": None,
        "created_at": "2024-01-01T00:00:00+00:00"
    }
    event = Event.from_dict(data)
    assert event.simulation_time == 1.0
    assert event.event_type == EventType.SIMULATION_STARTED


def test_event_validator_valid():
    """测试事件验证器 - 有效事件"""
    event = Event(
        event_type=EventType.SIMULATION_STARTED,
        simulation_time=0.0,
        data={"simulation_id": "test", "time_scale": 1.0}
    )
    assert EventValidator.is_valid(event) is True


def test_event_validator_invalid():
    """测试事件验证器 - 无效事件"""
    event = Event(
        event_type=EventType.SIMULATION_STARTED,
        simulation_time=0.0,
        data={}  # 缺少必需字段
    )
    assert EventValidator.is_valid(event) is False


def test_event_factory_method():
    """测试工厂方法创建事件"""
    event = Event.create(
        simulation_time=5.0,
        event_type=EventType.MARKER_CREATED,
        data={"label": "chapter-1"}
    )
    assert event.simulation_time == 5.0
    assert event.data["label"] == "chapter-1"


def test_event_immutability():
    """测试事件不可变性"""
    event = Event(
        event_type=EventType.SIMULATION_STARTED,
        simulation_time=0.0,
        data={}
    )
    # 事件是 frozen=True 的 dataclass，不能直接修改
    with pytest.raises(Exception):
        event.simulation_time = 10.0