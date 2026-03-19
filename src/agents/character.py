# agents/character.py
"""
角色模块

定义小说中的角色（Character），基于 ReplicantLife 的 Agent 模型。
角色的核心能力：
- 记忆系统（短期/长期）
- 目标驱动
- 决策能力
- 元认知

来源: ReplicantLife Agent 类
修改:
1. 移除 matrix 依赖（改为可选参数）
2. 移除游戏相关功能（kill, move 等）
3. 简化为小说角色所需的核心功能
"""

import random
import math
from collections import deque
from datetime import datetime
from typing import Optional, Any
import json


class Memory:
    """记忆对象
    
    表示角色的一条记忆。
    
    Attributes:
        kind: 记忆类型（observation, reflection, plan, meta 等）
        content: 记忆内容
        created_at: 创建时间
        last_accessed_at: 最后访问时间
        importance: 重要性分数（0-10）
        embedding: 嵌入向量（用于语义检索）
    """

    def __init__(
        self,
        kind: str,
        content: str,
        created_at: str,
        last_accessed_at: str,
        importance: int = 5,
        embedding: Optional[list[float]] = None
    ):
        self.kind = kind
        self.content = content
        self.created_at = created_at
        self.last_accessed_at = last_accessed_at
        self.importance = importance
        self.embedding = embedding
        self.relevancy_score = 0.0
        self.recency_score = 0.0
        self.overall_score = 0.0

    @staticmethod
    def calculateRelevanceScore(embedding1: Optional[list], embedding2: Optional[list]) -> float:
        """计算两个嵌入向量的相关性分数"""
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        # 简化的余弦相似度计算
        try:
            vec1 = embedding1
            vec2 = embedding2
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = math.sqrt(sum(a * a for a in vec1))
            norm2 = math.sqrt(sum(b * b for b in vec2))
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

    @staticmethod
    def calculateRecencyScore(last_accessed: str, current_time: str) -> float:
        """计算记忆的时效性分数"""
        try:
            last = datetime.fromisoformat(last_accessed.replace(" ", "T"))
            current = datetime.fromisoformat(current_time.replace(" ", "T"))
            delta = (current - last).total_seconds()
            # 指数衰减，越近期的记忆分数越高
            return math.exp(-delta / 86400)  # 1天衰减到 ~0.37
        except Exception:
            return 0.0

    def __str__(self) -> str:
        return f"[{self.kind}] {self.content}"

    def __repr__(self) -> str:
        return f"Memory(kind={self.kind}, importance={self.importance})"


class Character:
    """小说角色
    
    基于 ReplicantLife Agent 类，适配小说场景。
    移除了游戏相关功能（kill, move 等），保留了核心的认知能力。
    
    核心方法:
    - __init__: 初始化角色
    - getMemories: 获取相关记忆
    - addMemory: 添加新记忆
    - update_goals: 更新目标
    - decide: 做出决策
    - meta_cognize: 元认知反思
    - evaluate_progress: 评估目标进展
    
    Attributes:
        mid: 唯一标识符
        name: 名字
        description: 描述
        goal: 当前目标
        memory: 记忆列表
        short_memory: 短期记忆
        connections: 与其他角色的关系
        meta_questions: 元认知问题列表
    """

    def __init__(self, character_data: dict = None, matrix=None):
        """初始化角色
        
        Args:
            character_data: 角色数据字典
            matrix: 可选的外部引用（保持兼容性，但不强制依赖）
        """
        if character_data is None:
            character_data = {}
            
        import uuid
        
        # 基本信息
        self.mid = character_data.get("agent_id") or character_data.get("mid") or str(uuid.uuid4())
        self.name = character_data.get("name", "Unknown")
        self.description = character_data.get("description", "")
        self.goal = character_data.get("goal", "survive and thrive")
        self.kind = character_data.get("kind", "human")
        
        # 记忆系统
        self.memory: list[Memory] = character_data.get("memory", [])
        self.short_memory: list[str] = character_data.get("short_memory", [])
        self.spatial_memory = character_data.get("spatial_memory", [])
        
        # 关系网络
        self.connections: list[str] = character_data.get("connections", [])
        
        # 元认知
        self.meta_questions: list[str] = character_data.get("meta_questions", [])
        self.meta_rate = character_data.get("meta_rate", random.randint(0, 100))
        
        # 状态
        self.status = character_data.get("status", "active")
        self.plan = character_data.get("plan", None)
        
        # 保留 matrix 引用但可选
        self.matrix = matrix

    def addMemory(
        self,
        kind: str,
        content: str,
        timestamp: Optional[str] = None,
        score: Optional[int] = None,
        embedding: Optional[list[float]] = None
    ) -> Memory:
        """添加新记忆
        
        Args:
            kind: 记忆类型（observation, reflection, plan, meta 等）
            content: 记忆内容
            timestamp: 时间戳（可选）
            score: 重要性分数（可选）
            embedding: 嵌入向量（可选）
            
        Returns:
            创建的记忆对象
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if score is None:
            score = random.randint(3, 7)
            
        memory = Memory(
            kind=kind,
            content=content,
            created_at=timestamp,
            last_accessed_at=timestamp,
            importance=score,
            embedding=embedding
        )
        self.memory.append(memory)
        return memory

    def getMemories(
        self,
        context: Optional[str],
        timestamp: str,
        n: int = 20,
        include_short: bool = False
    ) -> list[Memory]:
        """获取相关记忆
        
        基于相关性、重要性和时效性检索记忆。
        
        Args:
            context: 查询上下文（用于语义匹配）
            timestamp: 当前时间戳
            n: 返回的记忆数量
            include_short: 是否包含短期记忆
            
        Returns:
            最相关的 n 条记忆
        """
        if len(self.memory) == 0:
            return []

        def make_range(values):
            if not values:
                return [0, 1]
            return [max(values), min(values)]

        def normalize(value, value_range):
            min_value = min(value_range)
            max_value = max(value_range)
            if min_value == max_value:
                return 0.0
            return (value - min_value) / (max_value - min_value)

        # 计算每条记忆的分数
        min_relevancy = float('inf')
        max_relevancy = float('-inf')
        min_recency = float('inf')
        max_recency = float('-inf')

        # 如果有上下文，计算相关性
        context_embedding = None
        if context:
            # TODO: 实际使用 LLM 嵌入
            context_embedding = None

        for mem in self.memory:
            relevancy_score = Memory.calculateRelevanceScore(mem.embedding, context_embedding)
            mem.relevancy_score = relevancy_score
            min_relevancy = min(min_relevancy, relevancy_score)
            max_relevancy = max(max_relevancy, relevancy_score)

            recency_score = Memory.calculateRecencyScore(mem.last_accessed_at, timestamp)
            mem.recency_score = recency_score
            min_recency = min(min_recency, recency_score)
            max_recency = max(max_recency, recency_score)

        # 计算范围
        relevancy_range = make_range([min_relevancy, max_relevancy])
        importance_range = make_range([mem.importance for mem in self.memory])
        recency_range = make_range([min_recency, max_recency])

        # 计算总分
        for mem in self.memory:
            overall_score = (
                normalize(mem.relevancy_score, relevancy_range) +
                normalize(mem.importance, importance_range) +
                normalize(mem.recency_score, recency_range)
            )
            mem.overall_score = overall_score

        # 按总分排序，返回前 n 条
        relevant_memories = []
        for mem in sorted(self.memory, key=lambda x: x.overall_score, reverse=True)[:n]:
            mem.last_accessed_at = timestamp
            relevant_memories.append(mem)

        return relevant_memories

    def update_goals(self, context: Optional[str] = None, llm_client=None) -> str:
        """更新角色目标
        
        基于最近的记忆重新评估目标。
        
        Args:
            context: 可选的上下文信息
            llm_client: LLM 客户端（可选，用于生成新目标）
            
        Returns:
            新的目标
        """
        # 简化版本：如果没有 LLM，保持原目标
        if llm_client is None:
            return self.goal
            
        # TODO: 使用 LLM 生成新目标
        # 相关记忆可用于指导目标更新
        return self.goal

    def decide(self, context: dict = None, llm_client=None) -> str:
        """做出决策
        
        基于当前状态和目标做出行为决策。
        
        Args:
            context: 决策上下文
            llm_client: LLM 客户端
            
        Returns:
            决策结果
        """
        if context is None:
            context = {}
        if llm_client is None:
            return "wait"
            
        # TODO: 使用 LLM 进行决策
        return "wait"

    def meta_cognize(self, timestamp: str, force: bool = False, llm_client=None) -> Optional[str]:
        """元认知反思
        
        对自身状态和目标进行深度思考。
        
        Args:
            timestamp: 时间戳
            force: 是否强制执行（忽略随机触发）
            llm_client: LLM 客户端
            
        Returns:
            反思结果（如果有）
        """
        if not force and random.randint(0, 100) > self.meta_rate:
            return None

        if not self.meta_questions:
            return None

        question = random.choice(self.meta_questions)
        
        if llm_client is None:
            # 没有 LLM，返回简单的反思
            return f"I wonder: {question}"
            
        # TODO: 使用 LLM 进行深度反思
        return f"I wonder: {question}"

    def evaluate_progress(self, opts: dict = None, llm_client=None) -> tuple[Optional[int], Optional[str]]:
        """评估目标进展
        
        Args:
            opts: 评估选项
            llm_client: LLM 客户端
            
        Returns:
            (分数, 解释) 元组
        """
        if opts is None:
            opts = {}
            
        if llm_client is None:
            return None, None
            
        # TODO: 使用 LLM 评估进展
        return None, None

    def getSelfContext(self) -> str:
        """获取角色的自我上下文
        
        用于生成提示词或与其他系统交互。
        
        Returns:
            自我描述字符串
        """
        return (
            f"Your name is {self.name}\n"
            f"Description: {self.description}\n"
            f"Goal: {self.goal}\n"
        )

    def __str__(self, verbose: bool = False) -> str:
        if verbose:
            return f"Character(name: {self.name}, goal: {self.goal}, status: {self.status})"
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"Character(name={self.name}, mid={self.mid})"


# 兼容性别名（保持与 ReplicantLife 的兼容性）
Agent = Character