"""书签数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Bookmark:
    """书签模型"""
    id: int                          # 唯一标识（自增）
    page_number: int                 # 书签所在页码
    chapter_index: int               # 所在章节索引
    chapter_name: str                # 章节名称
    preview_text: str                # 预览文本（最多50字符）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())  # 创建时间
    note: Optional[str] = None       # 用户备注（可选）
    
    def __post_init__(self):
        if self.page_number < 1:
            raise ValueError("页码必须大于0")
        if self.chapter_index < 0:
            raise ValueError("章节索引不能为负数")
        if len(self.preview_text) > 50:
            self.preview_text = self.preview_text[:50]
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'page_number': self.page_number,
            'chapter_index': self.chapter_index,
            'chapter_name': self.chapter_name,
            'preview_text': self.preview_text,
            'created_at': self.created_at,
            'note': self.note
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Bookmark':
        """从字典创建书签"""
        return cls(
            id=data['id'],
            page_number=data['page_number'],
            chapter_index=data['chapter_index'],
            chapter_name=data['chapter_name'],
            preview_text=data['preview_text'],
            created_at=data.get('created_at', datetime.now().isoformat()),
            note=data.get('note')
        )
