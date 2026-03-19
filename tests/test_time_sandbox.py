# tests/test_time_sandbox.py
"""时间沙箱测试"""

import pytest
import asyncio
from src.world.time_sandbox import TimeSandboxClock, ClockState


def test_time_sandbox_creation():
    """测试时间沙箱创建"""
    clock = TimeSandboxClock(time_scale=1.0)
    assert clock.get_time() == 0.0
    assert clock.get_time_scale() == 1.0
    assert clock.get_state() == ClockState.STOPPED


def test_time_sandbox_format_time():
    """测试时间格式化"""
    clock = TimeSandboxClock()
    
    # 1 小时
    clock.simulation_time = 3600
    assert clock.format_time() == "01:00:00"
    
    # 1 天 + 1 小时
    clock.simulation_time = 90000  # 25 小时
    assert clock.format_time() == "1d 01:00:00"


@pytest.mark.asyncio
async def test_time_sandbox_start_pause():
    """测试启动和暂停"""
    clock = TimeSandboxClock(time_scale=1.0)
    
    await clock.start()
    assert clock.get_state() == ClockState.RUNNING
    
    # 等待一小段时间让时间推进
    await asyncio.sleep(0.1)
    assert clock.get_time() > 0.0
    
    await clock.pause()
    assert clock.get_state() == ClockState.PAUSED
    
    # 暂停后时间应该停止
    paused_time = clock.get_time()
    await asyncio.sleep(0.1)
    assert clock.get_time() == paused_time


@pytest.mark.asyncio
async def test_time_sandbox_resume():
    """测试恢复"""
    clock = TimeSandboxClock(time_scale=1.0)
    
    await clock.start()
    await asyncio.sleep(0.05)
    await clock.pause()
    
    paused_time = clock.get_time()
    
    await clock.resume()
    assert clock.get_state() == ClockState.RUNNING
    
    await asyncio.sleep(0.05)
    assert clock.get_time() > paused_time


@pytest.mark.asyncio
async def test_time_sandbox_stop():
    """测试停止"""
    clock = TimeSandboxClock(time_scale=1.0)
    
    await clock.start()
    await asyncio.sleep(0.05)
    
    await clock.stop()
    assert clock.get_state() == ClockState.STOPPED


@pytest.mark.asyncio
async def test_time_sandbox_seek():
    """测试时间跳跃"""
    clock = TimeSandboxClock(time_scale=1.0)
    
    await clock.seek(100.0)
    assert clock.get_time() == 100.0
    
    # 负数应该被限制为 0
    await clock.seek(-10.0)
    assert clock.get_time() == 0.0


@pytest.mark.asyncio
async def test_time_sandbox_time_scale():
    """测试时间缩放"""
    clock = TimeSandboxClock(time_scale=10.0)  # 10 倍速
    
    await clock.start()
    await asyncio.sleep(0.1)
    await clock.pause()
    
    # 0.1 秒真实时间 = 约 1 秒模拟时间
    assert clock.get_time() >= 0.5  # 至少 0.5 秒


def test_time_sandbox_properties():
    """测试属性访问"""
    clock = TimeSandboxClock()
    
    clock.simulation_time = 50.0
    assert clock.simulation_time == 50.0
    
    clock.time_scale = 5.0
    assert clock.time_scale == 5.0
    
    with pytest.raises(ValueError):
        clock.time_scale = -1.0


def test_simulation_clock_alias():
    """测试兼容性别名"""
    from src.world.time_sandbox import SimulationClock
    
    # SimulationClock 应该是 TimeSandboxClock 的别名
    assert SimulationClock is TimeSandboxClock