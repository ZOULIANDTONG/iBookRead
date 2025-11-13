"""解析器工厂"""

from pathlib import Path
from typing import Optional

from .base import BaseParser
from .txt_parser import TxtParser
from .markdown_parser import MarkdownParser
from .epub_parser import EpubParser
from .mobi_parser import MobiParser
from ..core.format_detector import FormatDetector


class ParserFactory:
    """解析器工厂类"""
    
    # 格式到解析器的映射
    PARSER_MAP = {
        'txt': TxtParser,
        'markdown': MarkdownParser,
        'epub': EpubParser,
        'mobi': MobiParser
    }
    
    @classmethod
    def create_parser(cls, file_path: Path) -> Optional[BaseParser]:
        """
        根据文件类型创建对应的解析器
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析器实例，如果不支持则返回 None
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检测文件格式
        format_type = FormatDetector.detect(file_path)
        
        if format_type is None:
            return None
        
        # 获取对应的解析器类
        parser_class = cls.PARSER_MAP.get(format_type)
        
        if parser_class is None:
            return None
        
        # 创建解析器实例
        return parser_class(file_path)
    
    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """
        判断文件是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        try:
            format_type = FormatDetector.detect(file_path)
            return format_type in cls.PARSER_MAP
        except Exception:
            return False
