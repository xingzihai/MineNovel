# core/events.py
"""
事件模型模块

定义了事件系统的核心数据结构：
- EventType: 事件类型枚举
- Event: 不可变事件对象
- EventValidator: 事件验证器

事件是状态变化的记录，用于事件溯源和状态重建。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class EventValidationError(Exception):
    """事件验证失败时抛出的异常"""

    pass


class EventType(str, Enum):
    """事件类型枚举
    
    定义了系统中所有可能的事件类型。
    命名规则: <领域>.<动作>，如 simulation.started
    """

    # 模拟控制事件
    SIMULATION_STARTED = "simulation.started"      # 模拟开始
    SIMULATION_PAUSED = "simulation.paused"        # 模拟暂停
    SIMULATION_RESUMED = "simulation.resumed"      # 模拟恢复
    SIMULATION_STOPPED = "simulation.stopped"      # 模拟停止
    
    # 时间控制事件
    TIME_SCALED = "time.scaled"                    # 时间缩放
    TIME_SCALE_CHANGED = "simulation.time_scale_changed"  # 时间缩放改变
    
    # 标记事件
    MARKER_CREATED = "marker.created"              # 标记创建
    
    # 实体事件
    ENTITY_CREATED = "entity.created"              # 实体创建
    ENTITY_MOVED = "entity.moved"                  # 实体移动
    ENTITY_DESTROYED = "entity.destroyed"          # 实体销毁
    
    # 检查点事件
    CHECKPOINT_CREATED = "checkpoint.created"      # 检查点创建
    CHECKPOINT_RESTORED = "checkpoint.restored"    # 检查点恢复


@dataclass(frozen=True)
class Event:
    """不可变事件对象
    
    表示系统中的一个状态变化。事件一旦创建就不可修改，
    这是事件溯源的核心原则。
    
    Attributes:
        event_type: 事件类型
        simulation_time: 模拟时间（秒）
        data: 事件数据载荷
        metadata: 元数据（不影响状态的信息）
        event_id: 唯一标识符
        causation_id: 引起此事件的事件ID（因果链）
        correlation_id: 相关事件组ID（用于追踪）
        created_at: 真实世界时间戳
    """

    event_type: EventType | str
    simulation_time: float = 0.0  # 模拟时间，单位秒
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    causation_id: Optional[UUID] = None  # 哪个事件导致了此事件
    correlation_id: Optional[UUID] = None  # 关联一组相关事件
    created_at: Optional[datetime] = None  # 真实世界时间戳

    def __post_init__(self):
        """初始化后处理：自动设置时间戳和转换事件类型"""
        # 如果事件类型是字符串，尝试转换为 EventType
        if isinstance(self.event_type, str):
            try:
                object.__setattr__(self, "event_type", EventType(self.event_type))
            except ValueError:
                # 如果不是已知的 EventType，保持为字符串
                pass

        # 如果没有设置创建时间，使用当前时间
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))

    def __hash__(self) -> int:
        """使事件可哈希，用于集合和去重"""
        return hash(self.event_id)

    @property
    def timestamp(self) -> datetime:
        """获取事件创建时间戳"""
        return self.created_at or datetime.now(timezone.utc)

    @classmethod
    def create(
        cls,
        simulation_time: float,
        event_type: EventType | str,
        data: dict[str, Any],
        causation_id: Optional[UUID] = None,
    ) -> "Event":
        """工厂方法：创建事件
        
        Args:
            simulation_time: 模拟时间
            event_type: 事件类型
            data: 事件数据
            causation_id: 因果事件ID
            
        Returns:
            新创建的事件对象
        """
        return cls(
            simulation_time=simulation_time,
            event_type=event_type,
            data=data,
            causation_id=causation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示
        
        用于序列化和持久化。
        """
        return {
            "event_id": str(self.event_id),
            "simulation_time": self.simulation_time,
            "event_type": (
                self.event_type.value if isinstance(self.event_type, EventType) else self.event_type
            ),
            "data": self.data,
            "metadata": self.metadata,
            "causation_id": str(self.causation_id) if self.causation_id else None,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """从字典创建事件
        
        用于反序列化和重建事件。
        
        Args:
            data: 字典形式的事件数据
            
        Returns:
            重建的事件对象
        """
        return cls(
            event_id=UUID(data["event_id"]),
            simulation_time=data["simulation_time"],
            event_type=data["event_type"],
            data=data["data"],
            metadata=data.get("metadata", {}),
            causation_id=UUID(data["causation_id"]) if data.get("causation_id") else None,
            correlation_id=UUID(data["correlation_id"]) if data.get("correlation_id") else None,
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
        )


class EventValidator:
    """轻量级事件验证器
    
    根据事件类型的预定义模式验证事件数据。
    """

    # 每种事件类型的模式定义
    SCHEMAS: dict[str, dict[str, Any]] = {
        EventType.SIMULATION_STARTED: {
            "required": ["simulation_id", "time_scale"],
            "types": {"simulation_id": str, "time_scale": (int, float)},
        },
        EventType.SIMULATION_PAUSED: {
            "required": ["simulation_id", "paused_at"],
            "types": {"simulation_id": str, "paused_at": (int, float)},
        },
        EventType.SIMULATION_STOPPED: {
            "required": ["simulation_id"],
            "types": {"simulation_id": str},
        },
        EventType.TIME_SCALED: {
            "required": ["old_scale", "new_scale"],
            "types": {"old_scale": (int, float), "new_scale": (int, float)},
        },
        EventType.MARKER_CREATED: {
            "required": ["label"],
            "types": {"label": str},
        },
        EventType.ENTITY_CREATED: {
            "required": ["entity_id", "type", "position"],
            "types": {
                "entity_id": str,
                "type": str,
                "position": (list, tuple),
                "max_speed": (int, float),
            },
        },
        EventType.ENTITY_MOVED: {
            "required": ["entity_id", "position"],
            "types": {
                "entity_id": str,
                "position": (list, tuple),
                "velocity": (list, tuple),
                "heading": (int, float),
            },
        },
        EventType.ENTITY_DESTROYED: {
            "required": ["entity_id"],
            "types": {"entity_id": str},
        },
    }

    @classmethod
    def validate(cls, event: Event) -> None:
        """验证事件数据
        
        Args:
            event: 待验证的事件
            
        Raises:
            EventValidationError: 验证失败时抛出
        """
        event_type = event.event_type

        # 如果是字符串类型，尝试转换为 EventType
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                # 未知事件类型，跳过验证
                return

        schema = cls.SCHEMAS.get(event_type)
        if not schema:
            # 没有定义模式，跳过验证
            return

        # 检查必需字段
        required_fields = schema.get("required", [])
        for field_name in required_fields:
            if field_name not in event.data:
                raise EventValidationError(
                    f"Event {event_type.value} missing required field: {field_name}"
                )

        # 检查字段类型
        type_specs = schema.get("types", {})
        for field_name, expected_type in type_specs.items():
            if field_name in event.data:
                value = event.data[field_name]
                if not isinstance(value, expected_type):
                    raise EventValidationError(
                        f"Event {event_type.value} field '{field_name}' has wrong type: "
                        f"expected {expected_type}, got {type(value)}"
                    )

    @classmethod
    def is_valid(cls, event: Event) -> bool:
        """检查事件是否有效（不抛异常）
        
        Args:
            event: 待验证的事件
            
        Returns:
            True 如果有效，False 否则
        """
        try:
            cls.validate(event)
            return True
        except EventValidationError:
            return False