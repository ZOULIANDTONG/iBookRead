"""EPUB文档解析器"""

from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html

from .base import BaseParser
from ..models.document import Document, Chapter


class EpubParser(BaseParser):
    """EPUB文档解析器"""
    
    def parse(self) -> Document:
        """
        解析EPUB文档
        
        Returns:
            Document对象
        """
        try:
            # 加载 EPUB 文件
            book = epub.read_epub(str(self.file_path))
        except Exception as e:
            raise ValueError(f"无法解析EPUB文件: {e}")
        
        # 提取元数据
        title = self._extract_title(book)
        author = self._extract_author(book)
        language = self._extract_language(book)
        
        # 提取章节
        chapters = self._extract_chapters(book)
        
        # 如果没有章节，创建单章节
        if not chapters:
            chapters = [Chapter(
                index=0,
                title=title or self._get_default_title(),
                content="（无内容）",
                start_position=0
            )]
        
        # 创建文档对象
        document = Document(
            title=title or self._get_default_title(),
            chapters=chapters,
            author=author,
            language=language,
            metadata={'format': 'epub'}
        )
        
        return document
    
    def _extract_title(self, book: epub.EpubBook) -> str:
        """提取书名"""
        try:
            title = book.get_metadata('DC', 'title')
            if title and len(title) > 0:
                return str(title[0][0])
        except Exception:
            pass
        return ""
    
    def _extract_author(self, book: epub.EpubBook) -> str:
        """提取作者"""
        try:
            creator = book.get_metadata('DC', 'creator')
            if creator and len(creator) > 0:
                return str(creator[0][0])
        except Exception:
            pass
        return None
    
    def _extract_language(self, book: epub.EpubBook) -> str:
        """提取语言"""
        try:
            language = book.get_metadata('DC', 'language')
            if language and len(language) > 0:
                return str(language[0][0])
        except Exception:
            pass
        return None
    
    def _extract_chapters(self, book: epub.EpubBook) -> list[Chapter]:
        """提取章节"""
        chapters = []
        chapter_index = 0
        
        # 获取所有HTML项面（包括EpubHtml和EpubItem类型的HTML文件）
        items = []
        
        # 首先尝试从 spine 获取正确的阅读顺序
        for item_id, linear in book.spine:
            item = book.get_item_with_id(item_id)
            if item:
                items.append(item)
        
        # 如果 spine 为空，则获取所有HTML项面
        if not items:
            for item in book.get_items():
                # 检查是否为HTML内容
                if isinstance(item, epub.EpubHtml) or (
                    hasattr(item, 'get_name') and 
                    item.get_name().endswith(('.html', '.xhtml', '.htm'))
                ):
                    items.append(item)
        
        for item in items:
            try:
                # 跳过封面和导航页面
                item_name = item.get_name().lower()
                if any(skip in item_name for skip in ['cover', 'nav', 'toc']):
                    continue
                
                # 获取HTML内容
                html_content = item.get_content().decode('utf-8', errors='ignore')
                
                # 提取文本内容
                text_content = self._html_to_text(html_content)
                
                if not text_content.strip():
                    continue
                
                # 尝试从HTML中提取标题
                chapter_title = self._extract_chapter_title(html_content)
                if not chapter_title:
                    chapter_title = f"第 {chapter_index + 1} 章"
                
                # 创建章节
                chapter = Chapter(
                    index=chapter_index,
                    title=chapter_title,
                    content=text_content.strip(),
                    start_position=0
                )
                chapters.append(chapter)
                chapter_index += 1
                
            except Exception:
                continue
        
        return chapters
    
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
            soup = BeautifulSoup(html_content, 'xml')
            
            # 移除 script 和 style 标签
            for script in soup(['script', 'style']):
                script.decompose()
            
            # 获取文本
            text = soup.get_text()
            
            # 清理空白字符
            lines = [line.strip() for line in text.splitlines()]
            lines = [line for line in lines if line]
            
            return '\n\n'.join(lines)
            
        except Exception:
            # 如果解析失败，使用简单的文本提取
            return html.unescape(html_content)
    
    def _extract_chapter_title(self, html_content: str) -> str:
        """
        从HTML中提取章节标题
        
        Args:
            html_content: HTML内容
            
        Returns:
            章节标题
        """
        try:
            soup = BeautifulSoup(html_content, 'xml')
            
            # 尝试查找标题标签
            for tag in ['h1', 'h2', 'h3']:
                title_tag = soup.find(tag)
                if title_tag:
                    title = title_tag.get_text().strip()
                    if title:
                        return title
            
            # 尝试查找 title 标签
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                if title:
                    return title
                    
        except Exception:
            pass
        
        return ""
    
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
        return file_path.suffix.lower() == '.epub'
