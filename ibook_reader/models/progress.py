"""阅读进度数据模型"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ReadingProgress:
    """阅读进度模型"""
    file_path: str                   # 文档文件绝对路径
    file_hash: str                   # 文件MD5哈希值
    file_name: str                   # 文件名
    current_page: int                # 当前页码
    current_chapter: int             # 当前章节索引
    total_pages: int                 # 总页数
    total_chapters: int              # 总章节数
    last_read_time: str              # 最后阅读时间
    read_percentage: float = 0.0     # 阅读百分比
    
    def __post_init__(self):
        if self.current_page < 1:
            self.current_page = 1
        if self.current_chapter < 0:
            self.current_chapter = 0
        if self.total_pages < 1:
            raise ValueError("总页数必须大于0")
        if self.total_chapters < 1:
            raise ValueError("总章节数必须大于0")
        # 计算阅读百分比
        self.read_percentage = round((self.current_page / self.total_pages) * 100, 1)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'file_name': self.file_name,
            'current_page': self.current_page,
            'current_chapter': self.current_chapter,
            'total_pages': self.total_pages,
            'total_chapters': self.total_chapters,
            'last_read_time': self.last_read_time,
            'read_percentage': self.read_percentage
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReadingProgress':
        """从字典创建进度对象"""
        return cls(
            file_path=data['file_path'],
            file_hash=data['file_hash'],
            file_name=data['file_name'],
            current_page=data['current_page'],
            current_chapter=data['current_chapter'],
            total_pages=data['total_pages'],
            total_chapters=data['total_chapters'],
            last_read_time=data['last_read_time'],
            read_percentage=data.get('read_percentage', 0.0)
        )
    
    def update_position(self, page: int, chapter: int) -> None:
        """更新阅读位置"""
        self.current_page = max(1, min(page, self.total_pages))
        self.current_chapter = max(0, min(chapter, self.total_chapters - 1))
        self.read_percentage = round((self.current_page / self.total_pages) * 100, 1)
        self.last_read_time = datetime.now().isoformat()
