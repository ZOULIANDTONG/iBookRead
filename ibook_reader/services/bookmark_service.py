"""书签管理服务"""

from typing import List, Optional
from pathlib import Path

from ..models.bookmark import Bookmark
from ..models.document import Document
from ..core.paginator import Page
from ..config import Config
from ..utils.file_utils import read_json_file, write_json_file, get_file_hash
from ..utils.text_utils import extract_preview


class BookmarkService:
    """书签管理服务"""
    
    # 最大书签数量
    MAX_BOOKMARKS = 50
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化书签服务
        
        Args:
            config: 配置管理器实例
        """
        self.config = config or Config()
    
    def load_bookmarks(self, file_path: Path) -> List[Bookmark]:
        """
        加载文档的书签列表
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            书签列表
        """
        file_hash = get_file_hash(file_path)
        bookmark_file = self.config.get_bookmark_file(file_hash)
        
        if not bookmark_file.exists():
            return []
        
        data = read_json_file(bookmark_file)
        if not data or 'bookmarks' not in data:
            return []
        
        # 从字典列表转换为Bookmark对象列表
        bookmarks = []
        for item in data['bookmarks']:
            try:
                bookmark = Bookmark.from_dict(item)
                bookmarks.append(bookmark)
            except (KeyError, ValueError):
                # 跳过无效的书签数据
                continue
        
        return bookmarks
    
    def save_bookmarks(self, file_path: Path, bookmarks: List[Bookmark]) -> None:
        """
        保存书签列表
        
        Args:
            file_path: 文档文件路径
            bookmarks: 书签列表
        """
        file_hash = get_file_hash(file_path)
        bookmark_file = self.config.get_bookmark_file(file_hash)
        
        data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_hash': file_hash,
            'bookmarks': [bookmark.to_dict() for bookmark in bookmarks]
        }
        
        write_json_file(bookmark_file, data)
    
    def add_bookmark(
        self,
        file_path: Path,
        page: Page,
        document: Document,
        note: Optional[str] = None
    ) -> Bookmark:
        """
        添加书签
        
        Args:
            file_path: 文档文件路径
            page: 当前页面
            document: 文档对象
            note: 备注（可选）
            
        Returns:
            新添加的书签
            
        Raises:
            ValueError: 如果书签数量已达上限
        """
        # 加载现有书签
        bookmarks = self.load_bookmarks(file_path)
        
        # 检查数量限制
        if len(bookmarks) >= self.MAX_BOOKMARKS:
            raise ValueError(f"书签数量已达上限（{self.MAX_BOOKMARKS}个）")
        
        # 获取章节信息
        chapter = document.get_chapter(page.chapter_index)
        chapter_name = chapter.title if chapter else "未知章节"
        
        # 提取预览文本
        preview_text = extract_preview(page.content, max_length=50)
        
        # 生成新的书签ID
        next_id = max([b.id for b in bookmarks], default=0) + 1
        
        # 创建书签
        from datetime import datetime
        bookmark = Bookmark(
            id=next_id,
            page_number=page.page_number,
            chapter_index=page.chapter_index,
            chapter_name=chapter_name,
            preview_text=preview_text,
            created_at=datetime.now().isoformat(),
            note=note
        )
        
        # 添加到列表
        bookmarks.append(bookmark)
        
        # 保存
        self.save_bookmarks(file_path, bookmarks)
        
        return bookmark
    
    def remove_bookmark(self, file_path: Path, bookmark_id: int) -> bool:
        """
        删除书签
        
        Args:
            file_path: 文档文件路径
            bookmark_id: 书签ID
            
        Returns:
            是否删除成功
        """
        bookmarks = self.load_bookmarks(file_path)
        
        # 查找并删除
        original_count = len(bookmarks)
        bookmarks = [b for b in bookmarks if b.id != bookmark_id]
        
        if len(bookmarks) == original_count:
            return False  # 未找到要删除的书签
        
        # 保存
        if bookmarks:
            self.save_bookmarks(file_path, bookmarks)
        else:
            # 如果没有书签了，删除书签文件
            file_hash = get_file_hash(file_path)
            bookmark_file = self.config.get_bookmark_file(file_hash)
            if bookmark_file.exists():
                bookmark_file.unlink()
        
        return True
    
    def get_bookmark(self, file_path: Path, bookmark_id: int) -> Optional[Bookmark]:
        """
        获取指定书签
        
        Args:
            file_path: 文档文件路径
            bookmark_id: 书签ID
            
        Returns:
            书签对象，如果不存在返回None
        """
        bookmarks = self.load_bookmarks(file_path)
        
        for bookmark in bookmarks:
            if bookmark.id == bookmark_id:
                return bookmark
        
        return None
    
    def clear_all_bookmarks(self, file_path: Path) -> int:
        """
        清除文档的所有书签
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            清除的书签数量
        """
        bookmarks = self.load_bookmarks(file_path)
        count = len(bookmarks)
        
        if count > 0:
            file_hash = get_file_hash(file_path)
            bookmark_file = self.config.get_bookmark_file(file_hash)
            if bookmark_file.exists():
                bookmark_file.unlink()
        
        return count
