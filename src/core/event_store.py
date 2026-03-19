# core/event_store.py
"""
事件存储模块

提供追加式事件日志，支持：
- 事件持久化（异步）
- 事件重放（用于状态重建）
- 事件查询和过滤

使用 SQLite 作为存储后端，支持事务和批量操作。
"""

from typing import AsyncIterator, Optional
from uuid import UUID
import aiosqlite
import json
from .events import Event, EventType
from .exceptions import EventPersistenceError, EventRetrievalError
from .logging import get_logger

# 常量
_NOT_INITIALIZED_ERROR = "EventStore not initialized. Call initialize() first."


class EventStore:
    """追加式事件存储
    
    事件一旦写入就不可修改，这是事件溯源的核心原则。
    支持按模拟时间顺序查询和重放事件。
    
    Attributes:
        db_path: SQLite 数据库文件路径
    """

    def __init__(self, db_path: str):
        """初始化事件存储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        self.logger = get_logger(f"{__name__}.EventStore")

    async def initialize(self) -> None:
        """初始化数据库连接和模式
        
        创建事件表（如果不存在）。
        """
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                simulation_time REAL NOT NULL,
                event_type TEXT NOT NULL,
                data TEXT NOT NULL,
                metadata TEXT NOT NULL,
                causation_id TEXT,
                correlation_id TEXT,
                created_at TEXT NOT NULL
            )
        """
        )
        await self._db.commit()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._db:
            await self._db.close()
            self._db = None

    async def append(self, event: Event) -> None:
        """追加事件到存储
        
        Args:
            event: 要持久化的事件
            
        Raises:
            EventPersistenceError: 持久化失败时抛出
        """
        if not self._db:
            raise EventPersistenceError(_NOT_INITIALIZED_ERROR)

        try:
            await self._db.execute(
                """
                INSERT INTO events (
                    event_id, simulation_time, event_type, data, metadata,
                    causation_id, correlation_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(event.event_id),
                    event.simulation_time,
                    (
                        event.event_type.value
                        if isinstance(event.event_type, EventType)
                        else event.event_type
                    ),
                    json.dumps(event.data),
                    json.dumps(event.metadata),
                    str(event.causation_id) if event.causation_id else None,
                    str(event.correlation_id) if event.correlation_id else None,
                    event.created_at.isoformat(),
                ),
            )
            await self._db.commit()

            self.logger.debug(
                f"Event appended: id={event.event_id}, type={event.event_type}, time={event.simulation_time}"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to append event {event.event_id}: {e}"
            )
            raise EventPersistenceError(f"Failed to persist event {event.event_id}: {e}") from e

    async def append_batch(self, events: list[Event]) -> None:
        """批量追加事件（高效）
        
        Args:
            events: 事件列表
            
        Raises:
            EventPersistenceError: 持久化失败时抛出
        """
        if not events:
            return

        if not self._db:
            raise EventPersistenceError(_NOT_INITIALIZED_ERROR)

        try:
            await self._db.executemany(
                """
                INSERT INTO events (
                    event_id, simulation_time, event_type, data, metadata,
                    causation_id, correlation_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    (
                        str(e.event_id),
                        e.simulation_time,
                        e.event_type.value if isinstance(e.event_type, EventType) else e.event_type,
                        json.dumps(e.data),
                        json.dumps(e.metadata),
                        str(e.causation_id) if e.causation_id else None,
                        str(e.correlation_id) if e.correlation_id else None,
                        e.created_at.isoformat(),
                    )
                    for e in events
                ],
            )
            await self._db.commit()

            self.logger.info(
                f"Batch appended: {len(events)} events, time range: {events[0].simulation_time} - {events[-1].simulation_time}"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to append batch of {len(events)} events: {e}"
            )
            raise EventPersistenceError(f"Failed to persist batch of {len(events)} events: {e}") from e

    async def get_events(
        self,
        from_time: float = 0.0,
        to_time: Optional[float] = None,
        event_types: Optional[list[str]] = None,
    ) -> list[Event]:
        """获取事件列表（按模拟时间排序）
        
        Args:
            from_time: 起始时间（包含）
            to_time: 结束时间（包含），None 表示所有未来事件
            event_types: 事件类型过滤，None 表示所有类型
            
        Returns:
            匹配条件的事件列表
            
        Raises:
            EventRetrievalError: 检索失败时抛出
        """
        if not self._db:
            raise EventRetrievalError(_NOT_INITIALIZED_ERROR)

        try:
            query = "SELECT * FROM events WHERE simulation_time >= ?"
            params: list = [from_time]

            if to_time is not None:
                query += " AND simulation_time <= ?"
                params.append(to_time)

            if event_types:
                placeholders = ",".join("?" * len(event_types))
                query += f" AND event_type IN ({placeholders})"
                params.extend(event_types)

            query += " ORDER BY simulation_time ASC, created_at ASC"

            self.logger.debug(
                f"Querying events: from={from_time}, to={to_time}, types={event_types}"
            )

            cursor = await self._db.execute(query, params)
            rows = await cursor.fetchall()

            events = []
            for row in rows:
                from datetime import datetime

                events.append(
                    Event(
                        event_id=UUID(row[0]),
                        simulation_time=row[1],
                        event_type=EventType(row[2]),
                        data=json.loads(row[3]),
                        metadata=json.loads(row[4]),
                        causation_id=UUID(row[5]) if row[5] else None,
                        correlation_id=UUID(row[6]) if row[6] else None,
                        created_at=datetime.fromisoformat(row[7]),
                    )
                )

            self.logger.debug(f"Query complete: {len(events)} events returned")
            return events
        except Exception as e:
            self.logger.error(
                f"Failed to query events: {e}"
            )
            raise EventRetrievalError(f"Failed to retrieve events: {e}") from e

    async def stream_events(
        self,
        from_time: float = 0.0,
        to_time: Optional[float] = None,
        event_types: Optional[list[str]] = None,
    ) -> AsyncIterator[Event]:
        """流式获取事件（异步迭代器）
        
        Args:
            from_time: 起始时间
            to_time: 结束时间
            event_types: 事件类型过滤
            
        Yields:
            事件对象
        """
        events = await self.get_events(from_time, to_time, event_types)
        for event in events:
            yield event

    async def get_event_count(self) -> int:
        """获取事件总数"""
        if not self._db:
            return 0
        cursor = await self._db.execute("SELECT COUNT(*) FROM events")
        result = await cursor.fetchone()
        return result[0] if result else 0

    async def clear(self) -> None:
        """清空所有事件（仅用于测试）"""
        if not self._db:
            return
        await self._db.execute("DELETE FROM events")
        await self._db.commit()

    async def get_latest_time(self) -> Optional[float]:
        """获取最新事件的模拟时间"""
        if not self._db:
            return None
        cursor = await self._db.execute("SELECT MAX(simulation_time) FROM events")
        result = await cursor.fetchone()
        return result[0] if result and result[0] is not None else None