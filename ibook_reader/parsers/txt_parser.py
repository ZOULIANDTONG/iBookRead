"""TXT文档解析器"""

from pathlib import Path
import chardet

from .base import BaseParser
from ..models.document import Document, Chapter
from ..utils.text_utils import normalize_text


class TxtParser(BaseParser):
    """TXT文档解析器"""
    
    # 尝试的编码列表（按优先级）
    ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
    
    def parse(self) -> Document:
        """
        解析TXT文档
        
        Returns:
            Document对象
        """
        # 读取文件内容
        content = self._read_file()
        
        # 标准化文本
        content = normalize_text(content)
        
        # 创建单章节文档
        chapter = Chapter(
            index=0,
            title=self._get_default_title(),
            content=content,
            start_position=0
        )
        
        # 创建文档对象
        document = Document(
            title=self._get_default_title(),
            chapters=[chapter],
            metadata={
                'format': 'txt',
                'encoding': self._detected_encoding or 'unknown'
            }
        )
        
        return document
    
    def _read_file(self) -> str:
        """
        读取文件内容，自动检测编码
        
        Returns:
            文件内容
        """
        # 先读取部分内容检测编码
        with open(self.file_path, 'rb') as f:
            raw_data = f.read()
        
        # 使用 chardet 检测编码
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding')
        confidence = detected.get('confidence', 0)
        
        # 如果检测置信度较高，使用检测到的编码
        if encoding and confidence > 0.7:
            try:
                content = raw_data.decode(encoding)
                self._detected_encoding = encoding
                return content
            except Exception:
                pass
        
        # 否则依次尝试常用编码
        for enc in self.ENCODINGS:
            try:
                content = raw_data.decode(enc)
                self._detected_encoding = enc
                return content
            except Exception:
                continue
        
        # 最后使用 UTF-8 并忽略错误
        self._detected_encoding = 'utf-8'
        return raw_data.decode('utf-8', errors='ignore')
    
    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """
        判断是否可以解析该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否可以解析
        """
        if not file_path.exists():
            return False
        
        # 检查扩展名
        return file_path.suffix.lower() == '.txt'
