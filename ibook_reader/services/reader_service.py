"""阅读控制服务 - 核心控制器"""

from typing import Optional
from pathlib import Path

from ..models.document import Document
from ..core.paginator import Paginator, Page
from ..parsers.factory import ParserFactory
from .bookmark_service import BookmarkService
from .progress_service import ProgressService


class ReaderService:
    """阅读控制服务"""
    
    def __init__(
        self,
        bookmark_service: Optional[BookmarkService] = None,
        progress_service: Optional[ProgressService] = None
    ):
        """
        初始化阅读控制服务
        
        Args:
            bookmark_service: 书签服务实例
            progress_service: 进度服务实例
        """
        self.bookmark_service = bookmark_service or BookmarkService()
        self.progress_service = progress_service or ProgressService()
        
        # 当前状态
        self.file_path: Optional[Path] = None
        self.document: Optional[Document] = None
        self.paginator: Optional[Paginator] = None
        self.current_page: int = 1
        self.total_pages: int = 0
    
    def load_document(self, file_path: Path, rows: Optional[int] = None, cols: Optional[int] = None) -> bool:
        """
        加载文档
        
        Args:
            file_path: 文档文件路径
            rows: 终端行数
            cols: 终端列数
            
        Returns:
            是否加载成功
        """
        if not file_path.exists():
            return False
        
        # 创建解析器
        parser = ParserFactory.create_parser(file_path)
        if parser is None:
            return False
        
        # 解析文档
        try:
            self.document = parser.parse()
        except Exception:
            return False
        
        # 创建分页器
        self.paginator = Paginator(self.document, rows=rows, cols=cols)
        self.total_pages = self.paginator.get_total_pages()
        
        # 保存文件路径
        self.file_path = file_path
        
        # 尝试加载阅读进度
        progress = self.progress_service.load_progress(file_path)
        if progress:
            # 恢复进度
            self.current_page = min(progress.current_page, self.total_pages)
        else:
            # 从第一页开始
            self.current_page = 1
        
        return True
    
    def get_current_page(self) -> Optional[Page]:
        """
        获取当前页面
        
        Returns:
            当前页面对象
        """
        if self.paginator is None:
            return None
        
        return self.paginator.get_page(self.current_page)
    
    def next_page(self) -> bool:
        """
        翻到下一页
        
        Returns:
            是否成功翻页
        """
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_progress()
            return True
        return False
    
    def prev_page(self) -> bool:
        """
        翻到上一页
        
        Returns:
            是否成功翻页
        """
        if self.current_page > 1:
            self.current_page -= 1
            self._update_progress()
            return True
        return False
    
    def jump_to_page(self, page_number: int) -> bool:
        """
        跳转到指定页码
        
        Args:
            page_number: 目标页码
            
        Returns:
            是否成功跳转
        """
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self._update_progress()
            return True
        return False
    
    def next_chapter(self) -> bool:
        """
        跳到下一章
        
        Returns:
            是否成功跳转
        """
        if self.document is None or self.paginator is None:
            return False
        
        current_page_obj = self.get_current_page()
        if current_page_obj is None:
            return False
        
        # 获取下一章的索引
        next_chapter_index = current_page_obj.chapter_index + 1
        
        if next_chapter_index >= self.document.total_chapters:
            return False  # 已经是最后一章
        
        # 跳转到下一章的第一页
        next_chapter_page = self.paginator.get_page_by_chapter(next_chapter_index)
        if next_chapter_page:
            self.current_page = next_chapter_page.page_number
            self._update_progress()
            return True
        
        return False
    
    def prev_chapter(self) -> bool:
        """
        跳到上一章
        
        Returns:
            是否成功跳转
        """
        if self.document is None or self.paginator is None:
            return False
        
        current_page_obj = self.get_current_page()
        if current_page_obj is None:
            return False
        
        # 获取上一章的索引
        prev_chapter_index = current_page_obj.chapter_index - 1
        
        if prev_chapter_index < 0:
            return False  # 已经是第一章
        
        # 跳转到上一章的第一页
        prev_chapter_page = self.paginator.get_page_by_chapter(prev_chapter_index)
        if prev_chapter_page:
            self.current_page = prev_chapter_page.page_number
            self._update_progress()
            return True
        
        return False
    
    def jump_to_start(self) -> bool:
        """
        跳到开头
        
        Returns:
            是否成功跳转
        """
        return self.jump_to_page(1)
    
    def jump_to_end(self) -> bool:
        """
        跳到结尾
        
        Returns:
            是否成功跳转
        """
        return self.jump_to_page(self.total_pages)
    
    def add_bookmark(self, note: Optional[str] = None):
        """
        添加当前位置的书签
        
        Args:
            note: 备注
            
        Returns:
            新添加的书签
        """
        if self.file_path is None or self.document is None:
            raise ValueError("未加载文档")
        
        page = self.get_current_page()
        if page is None:
            raise ValueError("无效的页面")
        
        return self.bookmark_service.add_bookmark(
            self.file_path,
            page,
            self.document,
            note
        )
    
    def jump_to_bookmark(self, bookmark_id: int) -> bool:
        """
        跳转到书签位置
        
        Args:
            bookmark_id: 书签ID
            
        Returns:
            是否成功跳转
        """
        if self.file_path is None:
            return False
        
        bookmark = self.bookmark_service.get_bookmark(self.file_path, bookmark_id)
        if bookmark is None:
            return False
        
        return self.jump_to_page(bookmark.page_number)
    
    def update_terminal_size(self, rows: int, cols: int) -> None:
        """
        更新终端尺寸并重新分页
        
        Args:
            rows: 新的行数
            cols: 新的列数
        """
        if self.paginator is None or self.document is None:
            return
        
        # 记录当前位置（通过内容位置而不是页码）
        current_page_obj = self.get_current_page()
        if current_page_obj is None:
            return
        
        current_chapter = current_page_obj.chapter_index
        
        # 更新分页器
        self.paginator.update_terminal_size(rows, cols)
        self.total_pages = self.paginator.get_total_pages()
        
        # 恢复到相同章节的第一页
        new_page = self.paginator.get_page_by_chapter(current_chapter)
        if new_page:
            self.current_page = new_page.page_number
    
    def _update_progress(self) -> None:
        """更新阅读进度"""
        if self.file_path is None or self.document is None:
            return
        
        current_page_obj = self.get_current_page()
        if current_page_obj is None:
            return
        
        # 创建或更新进度
        progress = self.progress_service.load_progress(self.file_path)
        
        if progress is None:
            # 创建新进度
            progress = self.progress_service.create_progress(
                self.file_path,
                self.document,
                self.current_page,
                current_page_obj.chapter_index,
                self.total_pages
            )
        else:
            # 更新现有进度
            progress.update_position(self.current_page, current_page_obj.chapter_index)
        
        self.progress_service.save_progress(progress)
    
    def save_and_exit(self) -> None:
        """保存进度并退出"""
        self._update_progress()
