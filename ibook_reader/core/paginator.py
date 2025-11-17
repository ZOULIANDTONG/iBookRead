"""分页引擎"""

import os
from typing import List, Tuple, Optional
from ..models.document import Document, Chapter
from ..utils.text_utils import get_display_width


class Page:
    """页面模型"""
    
    def __init__(self, content: str, page_number: int, chapter_index: int):
        """
        初始化页面
        
        Args:
            content: 页面内容
            page_number: 页码（从1开始）
            chapter_index: 所属章节索引
        """
        self.content = content
        self.page_number = page_number
        self.chapter_index = chapter_index


class Paginator:
    """分页引擎"""
    
    # 小文档阈值（行数）
    SMALL_DOC_THRESHOLD = 1000
    
    # 大文档缓存窗口（前后各缓存的页数）
    CACHE_WINDOW = 3
    
    def __init__(self, document: Document, rows: Optional[int] = None, cols: Optional[int] = None):
        """
        初始化分页器
        
        Args:
            document: 文档对象
            rows: 终端行数（默认从环境获取）
            cols: 终端列数（默认从环境获取）
        """
        self.document = document
        self.terminal_rows = rows or self._get_terminal_rows()
        self.terminal_cols = cols or self._get_terminal_cols()
        
        # 计算可用显示区域
        self.available_rows = self._calculate_available_rows()
        self.available_cols = self._calculate_available_cols()
        
        # 页面缓存
        self._pages_cache: List[Page] = []
        self._cache_valid = False
        self._is_small_doc = False
    
    def _get_terminal_rows(self) -> int:
        """获取终端行数"""
        try:
            return os.get_terminal_size().lines
        except Exception:
            return 24  # 默认24行
    
    def _get_terminal_cols(self) -> int:
        """获取终端列数"""
        try:
            return os.get_terminal_size().columns
        except Exception:
            return 80  # 默认80列
    
    def _calculate_available_rows(self) -> int:
        """
        计算可用行数
        可用行数 = 终端总行数 - 标题栏(1) - 状态栏(1) - 上下边框(2) - 内边距(2)
        """
        return max(10, self.terminal_rows - 6)
    
    def _calculate_available_cols(self) -> int:
        """
        计算可用列数
        可用列数 = 终端总列数 - 左右边框(2) - 内边距(4)
        """
        return max(40, self.terminal_cols - 6)
    
    def update_terminal_size(self, rows: int, cols: int) -> None:
        """
        更新终端尺寸并重新计算分页
        
        Args:
            rows: 新的行数
            cols: 新的列数
        """
        self.terminal_rows = rows
        self.terminal_cols = cols
        self.available_rows = self._calculate_available_rows()
        self.available_cols = self._calculate_available_cols()
        
        # 使缓存失效
        self._cache_valid = False
        self._pages_cache.clear()
    
    def paginate(self) -> List[Page]:
        """
        执行分页
        
        Returns:
            页面列表
        """
        # 如果缓存有效，直接返回
        if self._cache_valid and self._pages_cache:
            return self._pages_cache
        
        pages = []
        page_number = 1
        
        # 遍历所有章节
        for chapter in self.document.chapters:
            # 对每个章节进行分页
            chapter_pages = self._paginate_chapter(chapter, page_number)
            pages.extend(chapter_pages)
            page_number += len(chapter_pages)
        
        # 判断是否为小文档
        total_lines = sum(len(page.content.splitlines()) for page in pages)
        self._is_small_doc = total_lines < self.SMALL_DOC_THRESHOLD
        
        # 如果是小文档，缓存所有页面
        if self._is_small_doc:
            self._pages_cache = pages
            self._cache_valid = True
        
        return pages
    
    def _paginate_chapter(self, chapter: Chapter, start_page_number: int) -> List[Page]:
        """
        对单个章节进行分页
        
        Args:
            chapter: 章节对象
            start_page_number: 起始页码
            
        Returns:
            章节的页面列表
        """
        pages = []
        page_number = start_page_number
        
        # 按行分割内容，保留原始换行结构
        lines = chapter.content.split('\n')
        current_lines = []
        
        for line in lines:
            # 对每行进行自动换行
            wrapped_lines = self._wrap_line(line)
            
            # 将换行后的行添加到当前页
            for wrapped_line in wrapped_lines:
                current_lines.append(wrapped_line)
                
                # 如果当前页已满，创建新页
                if len(current_lines) >= self.available_rows:
                    page_content = '\n'.join(current_lines[:self.available_rows])
                    pages.append(Page(page_content, page_number, chapter.index))
                    page_number += 1
                    current_lines = current_lines[self.available_rows:]
        
        # 创建最后一页（如果有剩余内容）
        if current_lines:
            # 移除末尾多余的空行
            while current_lines and not current_lines[-1]:
                current_lines.pop()
            
            if current_lines:
                page_content = '\n'.join(current_lines)
                pages.append(Page(page_content, page_number, chapter.index))
        
        return pages
    
    def _wrap_line(self, line: str) -> List[str]:
        """
        对单行进行自动换行
        
        Args:
            line: 单行文本
            
        Returns:
            换行后的文本列表
        """
        # 空行直接返回
        if not line.strip():
            return [line]
        
        lines = []
        current_line = []
        current_width = 0
        
        # 遍历行中的每个字符
        for char in line:
            char_width = get_display_width(char)
            
            # 检查是否需要换行
            if current_width + char_width > self.available_cols:
                # 尝试在合适的位置断行
                if current_line:
                    lines.append(''.join(current_line))
                    current_line = [char]
                    current_width = char_width
                else:
                    # 单个字符就超过宽度，强制添加
                    current_line.append(char)
                    lines.append(''.join(current_line))
                    current_line = []
                    current_width = 0
            else:
                current_line.append(char)
                current_width += char_width
        
        # 添加最后一行
        if current_line:
            lines.append(''.join(current_line))
        
        return lines if lines else [line]
    
    def get_page(self, page_number: int) -> Optional[Page]:
        """
        获取指定页码的页面
        
        Args:
            page_number: 页码（从1开始）
            
        Returns:
            页面对象，如果页码无效返回None
        """
        pages = self.paginate()
        
        if 1 <= page_number <= len(pages):
            return pages[page_number - 1]
        
        return None
    
    def get_total_pages(self) -> int:
        """
        获取总页数
        
        Returns:
            总页数
        """
        pages = self.paginate()
        return len(pages)
    
    def get_page_by_chapter(self, chapter_index: int) -> Optional[Page]:
        """
        获取指定章节的第一页
        
        Args:
            chapter_index: 章节索引（从0开始）
            
        Returns:
            章节第一页，如果章节不存在返回None
        """
        if chapter_index < 0 or chapter_index >= self.document.total_chapters:
            return None
        
        pages = self.paginate()
        
        # 查找该章节的第一页
        for page in pages:
            if page.chapter_index == chapter_index:
                return page
        
        return None
    
    def find_page_position(self, page_number: int) -> Optional[Tuple[int, int]]:
        """
        查找页面位置（章节索引和章内页码）
        
        Args:
            page_number: 页码（从1开始）
            
        Returns:
            (章节索引, 章内页码) 元组，如果页码无效返回None
        """
        page = self.get_page(page_number)
        if page is None:
            return None
        
        # 计算章内页码
        pages = self.paginate()
        chapter_start_page = 1
        
        for p in pages:
            if p.chapter_index == page.chapter_index:
                chapter_start_page = p.page_number
                break
        
        chapter_page = page_number - chapter_start_page + 1
        
        return (page.chapter_index, chapter_page)
