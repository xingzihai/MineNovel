# world/time_sandbox.py
"""
时间沙箱模块

提供可控的模拟时间系统，支持：
- 时间加速/减速
- 暂停/恢复
- 时间跳跃

用于小说世界的时间模拟，可以快速推进时间或暂停以观察细节。
"""

from dataclasses import dataclass
from typing import Optional
import asyncio
from datetime import datetime, timezone
from enum import Enum


class ClockState(str, Enum):
    """时钟状态枚举"""

    STOPPED = "stopped"  # 已停止
    RUNNING = "running"  # 运行中
    PAUSED = "paused"    # 已暂停


@dataclass
class TimeState:
    """时间状态数据类
    
    Attributes:
        current_time: 当前模拟时间（秒）
        time_scale: 时间缩放倍率（1.0 = 实时，10.0 = 10倍速）
        is_running: 是否正在运行
        started_at: 开始运行的真实时间
    """

    current_time: float  # 模拟时间（秒）
    time_scale: float    # 时间缩放倍率
    is_running: bool
    started_at: Optional[datetime] = None


class TimeSandboxClock:
    """时间沙箱时钟
    
    管理连续的模拟时间，支持变量缩放。
    适用于需要精确控制时间流速的场景。
    
    原名: SimulationClock (来自 Strategos)
    改名原因: 更符合小说场景的时间沙箱概念
    
    Example:
        clock = TimeSandboxClock(time_scale=60.0)  # 1秒 = 1分钟模拟时间
        await clock.start()
        # ... 故事进行中 ...
        await clock.pause()  # 暂停以观察细节
        print(clock.format_time())  # "01:23:45"
    """

    def __init__(self, time_scale: float = 1.0):
        """初始化时间沙箱
        
        Args:
            time_scale: 时间缩放倍率（默认 1.0 = 实时）
        """
        self._time_state = TimeState(current_time=0.0, time_scale=time_scale, is_running=False)
        self._last_update: Optional[float] = None  # asyncio 循环时间
        self._update_task: Optional[asyncio.Task] = None
        self._clock_state = ClockState.STOPPED

    async def start(self) -> None:
        """开始时间流动"""
        if self._time_state.is_running:
            return

        self._time_state.is_running = True
        self._clock_state = ClockState.RUNNING
        self._time_state.started_at = datetime.now(timezone.utc)
        self._last_update = asyncio.get_event_loop().time()

        # 启动更新循环
        self._update_task = asyncio.create_task(self._update_loop())
        await asyncio.sleep(0)  # 让出控制权以允许异步执行

    async def pause(self) -> None:
        """暂停时间流动"""
        self._time_state.is_running = False
        self._clock_state = ClockState.PAUSED
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                # 任务成功取消，清理
                pass
            finally:
                self._update_task = None

    async def resume(self) -> None:
        """从暂停状态恢复"""
        if self._clock_state == ClockState.PAUSED:
            await self.start()

    async def stop(self) -> None:
        """完全停止时钟"""
        self._time_state.is_running = False
        self._clock_state = ClockState.STOPPED
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                # 任务成功取消，清理
                pass
            finally:
                self._update_task = None

    async def seek(self, target_time: float) -> None:
        """跳跃到指定模拟时间
        
        Args:
            target_time: 目标时间（秒）
        """
        was_running = self._time_state.is_running
        if was_running:
            await self.pause()

        self._time_state.current_time = max(0.0, target_time)

        if was_running:
            await self.start()

    async def set_time_scale(self, scale: float) -> None:
        """设置时间缩放倍率
        
        Args:
            scale: 新的缩放倍率（必须为正数）
            
        Raises:
            ValueError: 如果 scale <= 0
        """
        if scale <= 0:
            raise ValueError("Time scale must be positive")
        self._time_state.time_scale = scale

    async def tick(self) -> float:
        """强制更新模拟时间并返回当前时间"""
        if not self._time_state.is_running:
            return self.get_time()

        await asyncio.sleep(0)  # 让更新循环有机会运行
        return self.get_time()

    async def _update_loop(self) -> None:
        """内部循环：推进模拟时间"""
        while self._time_state.is_running:
            await asyncio.sleep(0.016)  # ~60 FPS 更新率

            current_real_time = asyncio.get_event_loop().time()
            if self._last_update is not None:
                delta_real = current_real_time - self._last_update
                delta_sim = delta_real * self._time_state.time_scale
                self._time_state.current_time += delta_sim

            self._last_update = current_real_time

    def get_time(self) -> float:
        """获取当前模拟时间（秒）"""
        return self._time_state.current_time

    def get_time_scale(self) -> float:
        """获取当前时间缩放倍率"""
        return self._time_state.time_scale

    def get_state(self) -> ClockState:
        """获取当前时钟状态"""
        return self._clock_state

    @property
    def state(self) -> ClockState:
        """时钟状态属性"""
        return self._clock_state

    @property
    def simulation_time(self) -> float:
        """模拟时间属性（get_time 的别名）"""
        return self.get_time()

    @simulation_time.setter
    def simulation_time(self, value: float) -> None:
        """直接设置模拟时间"""
        self._time_state.current_time = max(0.0, value)

    @property
    def time_scale(self) -> float:
        """时间缩放属性"""
        return self.get_time_scale()

    @time_scale.setter
    def time_scale(self, value: float) -> None:
        """直接设置时间缩放"""
        if value <= 0:
            raise ValueError("Time scale must be positive")
        self._time_state.time_scale = value

    def format_time(self) -> str:
        """格式化时间为 HH:MM:SS 或 Xd HH:MM:SS
        
        Returns:
            格式化的时间字符串
        """
        total_seconds = int(self._time_state.current_time)
        days = total_seconds // 86400
        remainder = total_seconds % 86400
        hours = remainder // 3600
        minutes = (remainder % 3600) // 60
        seconds = remainder % 60

        if days > 0:
            return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# 兼容性别名（保持与 Strategos 的兼容性）
SimulationClock = TimeSandboxClock