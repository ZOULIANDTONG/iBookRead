"""解析器基类"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..models.document import Document


class BaseParser(ABC):
    """文档解析器基类"""
    
    def __init__(self, file_path: Path):
        """
        初始化解析器
        
        Args:
            file_path: 文件路径
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        self.file_path = file_path
        self.file_name = file_path.name
    
    @abstractmethod
    def parse(self) -> Document:
        """
        解析文档
        
        Returns:
            Document对象
        """
        pass
    
    @classmethod
    @abstractmethod
    def can_parse(cls, file_path: Path) -> bool:
        """
        判断是否可以解析该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否可以解析
        """
        pass
    
    def _get_default_title(self) -> str:
        """
        获取默认标题（使用文件名）
        
        Returns:
            文件名（不含扩展名）
        """
        return self.file_path.stem
