"""文档格式检测器"""

from pathlib import Path
from typing import Optional


class FormatDetector:
    """文档格式检测器"""
    
    # 支持的扩展名映射
    EXTENSION_MAP = {
        '.txt': 'txt',
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.epub': 'epub',
        '.mobi': 'mobi',
        '.azw': 'mobi',
        '.azw3': 'mobi'
    }
    
    # 文件魔数标识
    MAGIC_NUMBERS = {
        b'PK\x03\x04': 'epub',  # ZIP 文件头（EPUB 是 ZIP 格式）
        b'BOOKMOBI': 'mobi',    # MOBI 文件标识
    }
    
    @classmethod
    def detect(cls, file_path: Path) -> Optional[str]:
        """
        检测文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            格式类型（'txt', 'markdown', 'epub', 'mobi'）或 None
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 1. 先通过扩展名检测
        ext = file_path.suffix.lower()
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]
        
        # 2. 通过文件魔数检测
        try:
            with open(file_path, 'rb') as f:
                header = f.read(60)  # 读取前60字节
                
                for magic, format_type in cls.MAGIC_NUMBERS.items():
                    if header.startswith(magic):
                        return format_type
                
                # 检查是否包含 MOBI 标识（可能不在开头）
                if b'BOOKMOBI' in header:
                    return 'mobi'
        except Exception:
            pass
        
        # 3. 默认作为文本文件处理
        return 'txt'
    
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
            format_type = cls.detect(file_path)
            return format_type is not None
        except Exception:
            return False
