# core/exceptions.py
# 异常定义模块

"""MineNovel 核心异常类型"""


class EventPersistenceError(Exception):
    """事件持久化失败时抛出"""

    pass


class EventRetrievalError(Exception):
    """事件检索失败时抛出"""

    pass