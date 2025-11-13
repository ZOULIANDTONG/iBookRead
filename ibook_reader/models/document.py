"""文档数据模型"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Chapter:
    """章节模型"""
    index: int                    # 章节序号（从0开始）
    title: str                    # 章节标题
    content: str                  # 章节纯文本内容
    start_position: int = 0       # 在全文中的起始位置
    
    def __post_init__(self):
        if self.index < 0:
            raise ValueError("章节索引不能为负数")
        if not self.title:
            self.title = f"第 {self.index + 1} 章"


@dataclass
class Document:
    """文档内容模型"""
    title: str                              # 文档标题
    chapters: List[Chapter] = field(default_factory=list)  # 章节列表
    author: Optional[str] = None            # 作者信息
    language: Optional[str] = None          # 文档语言
    metadata: Dict[str, str] = field(default_factory=dict)  # 其他元数据
    
    def __post_init__(self):
        if not self.title:
            raise ValueError("文档标题不能为空")
        if not self.chapters:
            raise ValueError("文档必须至少包含一个章节")
    
    @property
    def total_chapters(self) -> int:
        """获取总章节数"""
        return len(self.chapters)
    
    def get_chapter(self, index: int) -> Optional[Chapter]:
        """获取指定索引的章节"""
        if 0 <= index < len(self.chapters):
            return self.chapters[index]
        return None
    
    @property
    def full_content(self) -> str:
        """获取完整文档内容"""
        return '\n\n'.join(chapter.content for chapter in self.chapters)
