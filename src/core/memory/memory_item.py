# core/memory/memory_item.py
"""
Memory Item Definition
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import uuid


class MemoryLayer(str, Enum):
    """Memory layer types"""
    L1_IDENTITY = "L1"      # Identity layer: world rules, character definitions
    L2_RUNTIME = "L2"       # Runtime layer: state changes, pending matters
    L3_LOG = "L3"           # Log layer: chapter summaries


class MemoryCategory(str, Enum):
    """Memory categories"""
    WORLD = "world"           # World rules, setting
    CHARACTER = "character"   # Character info
    PLOT = "plot"             # Plot elements
    ITEM = "item"             # Items, assets
    LOCATION = "location"     # Places, locations
    EVENT = "event"           # Events
    RELATIONSHIP = "relationship"  # Character relationships
    OTHER = "other"           # Other


@dataclass
class MemoryItem:
    """Memory item"""
    id: str
    layer: MemoryLayer
    category: MemoryCategory
    content: str
    importance: int = 5              # 1-10
    source_chapter: int = 0          # Source chapter (0 = initial setting)
    created_at: str = ""             # ISO timestamp
    updated_at: str = ""             # ISO timestamp
    expires_chapter: Optional[int] = None  # Chapter when memory expires
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.id:
            self.id = f"mem_{uuid.uuid4().hex[:8]}"
    
    @classmethod
    def create(
        cls,
        layer: MemoryLayer,
        category: MemoryCategory,
        content: str,
        importance: int = 5,
        source_chapter: int = 0,
        **kwargs
    ) -> "MemoryItem":
        """Create a new memory item"""
        return cls(
            id=f"mem_{uuid.uuid4().hex[:8]}",
            layer=layer,
            category=category,
            content=content,
            importance=importance,
            source_chapter=source_chapter,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "layer": self.layer.value,
            "category": self.category.value,
            "content": self.content,
            "importance": self.importance,
            "source_chapter": self.source_chapter,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_chapter": self.expires_chapter,
            "metadata": self.metadata,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create from dictionary"""
        return cls(
            id=data.get("id", f"mem_{uuid.uuid4().hex[:8]}"),
            layer=MemoryLayer(data.get("layer", "L3")),
            category=MemoryCategory(data.get("category", "other")),
            content=data.get("content", ""),
            importance=data.get("importance", 5),
            source_chapter=data.get("source_chapter", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            expires_chapter=data.get("expires_chapter"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )
    
    def is_expired(self, current_chapter: int) -> bool:
        """Check if memory is expired"""
        if self.expires_chapter is None:
            return False
        return current_chapter > self.expires_chapter
    
    def update(self, content: str = None, importance: int = None, **kwargs) -> None:
        """Update memory item"""
        if content is not None:
            self.content = content
        if importance is not None:
            self.importance = importance
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()
    
    def __str__(self) -> str:
        return f"[{self.layer.value}:{self.category.value}] {self.content[:50]}..."
    
    def __repr__(self) -> str:
        return f"MemoryItem(id={self.id}, layer={self.layer.value}, category={self.category.value})"