# tests/test_character.py
"""角色模块测试"""

import pytest
from src.agents.character import Character, Memory


def test_character_creation():
    """测试角色创建"""
    char = Character({"name": "Alice", "description": "A curious girl"})
    
    assert char.name == "Alice"
    assert char.description == "A curious girl"
    assert char.status == "active"
    assert char.mid is not None


def test_character_with_full_data():
    """测试完整数据创建"""
    char = Character({
        "agent_id": "char-001",
        "name": "Bob",
        "description": "A brave knight",
        "goal": "Protect the kingdom",
        "kind": "human",
        "status": "active"
    })
    
    assert char.mid == "char-001"
    assert char.name == "Bob"
    assert char.goal == "Protect the kingdom"


def test_character_add_memory():
    """测试添加记忆"""
    char = Character({"name": "Test"})
    
    mem = char.addMemory(
        kind="observation",
        content="I saw a rabbit",
        timestamp="2024-01-01 12:00:00",
        score=7
    )
    
    assert len(char.memory) == 1
    assert mem.content == "I saw a rabbit"
    assert mem.kind == "observation"
    assert mem.importance == 7


def test_character_get_memories():
    """测试获取记忆"""
    char = Character({"name": "Test"})
    
    # 添加多条记忆
    for i in range(5):
        char.addMemory(
            kind="observation",
            content=f"Memory {i}",
            timestamp=f"2024-01-01 {12+i:02d}:00:00",
            score=i + 1
        )
    
    memories = char.getMemories(None, "2024-01-01 15:00:00", n=3)
    assert len(memories) == 3


def test_character_get_self_context():
    """测试自我上下文"""
    char = Character({
        "name": "Alice",
        "description": "Curious and brave",
        "goal": "Find the white rabbit"
    })
    
    context = char.getSelfContext()
    assert "Alice" in context
    assert "Curious and brave" in context
    assert "Find the white rabbit" in context


def test_character_str():
    """测试字符串表示"""
    char = Character({"name": "Alice"})
    
    assert str(char) == "Alice"
    assert "Alice" in repr(char)


def test_memory_creation():
    """测试记忆对象创建"""
    mem = Memory(
        kind="reflection",
        content="I should be more careful",
        created_at="2024-01-01 12:00:00",
        last_accessed_at="2024-01-01 12:00:00",
        importance=8
    )
    
    assert mem.kind == "reflection"
    assert mem.content == "I should be more careful"
    assert mem.importance == 8


def test_memory_relevance_score():
    """测试记忆相关性计算"""
    # None 嵌入应该返回 0
    score = Memory.calculateRelevanceScore(None, None)
    assert score == 0.0
    
    # 简单的向量
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    score = Memory.calculateRelevanceScore(vec1, vec2)
    assert abs(score - 1.0) < 0.01  # 相同向量应该接近 1


def test_memory_recency_score():
    """测试记忆时效性计算"""
    # 当前时间
    now = "2024-01-01 12:00:00"
    score = Memory.calculateRecencyScore(now, now)
    assert score > 0.9  # 刚访问的记忆分数应该很高
    
    # 一天前
    old = "2024-01-01 12:00:00"
    current = "2024-01-02 12:00:00"
    score = Memory.calculateRecencyScore(old, current)
    assert 0 < score < 0.5  # 一天前衰减


def test_character_meta_cognize():
    """测试元认知"""
    char = Character({
        "name": "Test",
        "meta_questions": ["What is my purpose?", "Why am I here?"],
        "meta_rate": 100  # 强制触发
    })
    
    result = char.meta_cognize("2024-01-01 12:00:00", force=True)
    
    # 应该返回一个反思结果
    assert result is not None


def test_character_without_matrix():
    """测试不依赖 matrix 的角色"""
    char = Character({"name": "Independent"})
    
    # 所有方法都应该可以正常调用，不依赖 matrix
    char.addMemory("observation", "Test", "2024-01-01 12:00:00")
    memories = char.getMemories(None, "2024-01-01 12:00:00")
    
    assert len(memories) == 1


def test_agent_alias():
    """测试 Agent 别名兼容性"""
    from src.agents.character import Agent
    
    # Agent 应该是 Character 的别名
    agent = Agent({"name": "Test"})
    assert isinstance(agent, Character)