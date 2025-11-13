"""MOBI文档解析器"""

from pathlib import Path
from bs4 import BeautifulSoup
import html

from .base import BaseParser
from ..models.document import Document, Chapter


class MobiParser(BaseParser):
    """MOBI文档解析器"""
    
    def parse(self) -> Document:
        """
        解析MOBI文档
        
        Returns:
            Document对象
        """
        try:
            # 尝试使用 mobi 库解析
            import mobi
            
            tempdir, filepath = mobi.extract(str(self.file_path))
            
            # 读取提取的HTML文件
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # 提取文本内容
            text_content = self._html_to_text(html_content)
            
            # 创建单章节文档
            chapter = Chapter(
                index=0,
                title=self._get_default_title(),
                content=text_content.strip(),
                start_position=0
            )
            
            # 创建文档对象
            document = Document(
                title=self._get_default_title(),
                chapters=[chapter],
                metadata={'format': 'mobi'}
            )
            
            return document
            
        except ImportError:
            # 如果没有安装 mobi 库，降级处理
            return self._fallback_parse()
        except Exception as e:
            # 解析失败，降级处理
            return self._fallback_parse()
    
    def _fallback_parse(self) -> Document:
        """
        降级解析方法（作为纯文本处理）
        
        Returns:
            Document对象
        """
        try:
            # 尝试作为文本读取
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 创建单章节文档
            chapter = Chapter(
                index=0,
                title=self._get_default_title(),
                content=content.strip() if content.strip() else "（无法解析文件内容）",
                start_position=0
            )
            
        except Exception:
            # 完全失败，返回错误提示
            chapter = Chapter(
                index=0,
                title=self._get_default_title(),
                content="（无法解析MOBI文件，请安装 mobi 库：pip install mobi）",
                start_position=0
            )
        
        # 创建文档对象
        document = Document(
            title=self._get_default_title(),
            chapters=[chapter],
            metadata={'format': 'mobi', 'parsed': 'fallback'}
        )
        
        return document
    
    def _html_to_text(self, html_content: str) -> str:
        """
        将HTML转换为纯文本
        
        Args:
            html_content: HTML内容
            
        Returns:
            纯文本内容
        """
        try:
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 移除 script 和 style 标签
            for script in soup(['script', 'style']):
                script.decompose()
            
            # 获取文本
            text = soup.get_text(separator='\n')
            
            # 清理空白字符，但保留换行
            lines = [line.strip() for line in text.splitlines()]
            # 去除完全空白的行
            lines = [line if line else '' for line in lines]
            
            # 合并连续的空行
            result = []
            prev_empty = False
            for line in lines:
                if line == '':
                    if not prev_empty:
                        result.append('')
                    prev_empty = True
                else:
                    result.append(line)
                    prev_empty = False
            
            return '\n'.join(result)
            
        except Exception:
            # 如果解析失败，使用简单的文本提取
            return html.unescape(html_content)
    
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
        ext = file_path.suffix.lower()
        return ext in ['.mobi', '.azw', '.azw3']
