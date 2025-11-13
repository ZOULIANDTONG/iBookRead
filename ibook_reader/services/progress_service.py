"""阅读进度管理服务"""

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from ..models.progress import ReadingProgress
from ..models.document import Document
from ..config import Config
from ..utils.file_utils import read_json_file, write_json_file, get_file_hash


class ProgressService:
    """阅读进度管理服务"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化进度服务
        
        Args:
            config: 配置管理器实例
        """
        self.config = config or Config()
    
    def load_progress(self, file_path: Path) -> Optional[ReadingProgress]:
        """
        加载文档的阅读进度
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            阅读进度对象，如果不存在返回None
        """
        file_hash = get_file_hash(file_path)
        
        # 读取进度文件
        data = read_json_file(self.config.progress_file)
        if not data or 'documents' not in data:
            return None
        
        # 查找匹配的进度记录
        for doc_data in data['documents']:
            if doc_data.get('file_hash') == file_hash:
                try:
                    progress = ReadingProgress.from_dict(doc_data)
                    
                    # 验证文件路径是否匹配
                    if Path(progress.file_path) == file_path:
                        return progress
                except (KeyError, ValueError):
                    continue
        
        return None
    
    def save_progress(self, progress: ReadingProgress) -> None:
        """
        保存阅读进度
        
        Args:
            progress: 阅读进度对象
        """
        # 读取现有进度数据
        data = read_json_file(self.config.progress_file, default={'documents': []})
        
        if 'documents' not in data:
            data['documents'] = []
        
        # 查找并更新现有记录
        updated = False
        for i, doc_data in enumerate(data['documents']):
            if doc_data.get('file_hash') == progress.file_hash:
                data['documents'][i] = progress.to_dict()
                updated = True
                break
        
        # 如果不存在，添加新记录
        if not updated:
            data['documents'].append(progress.to_dict())
        
        # 保存
        write_json_file(self.config.progress_file, data)
    
    def create_progress(
        self,
        file_path: Path,
        document: Document,
        current_page: int,
        current_chapter: int,
        total_pages: int
    ) -> ReadingProgress:
        """
        创建阅读进度
        
        Args:
            file_path: 文档文件路径
            document: 文档对象
            current_page: 当前页码
            current_chapter: 当前章节索引
            total_pages: 总页数
            
        Returns:
            阅读进度对象
        """
        file_hash = get_file_hash(file_path)
        
        progress = ReadingProgress(
            file_path=str(file_path),
            file_hash=file_hash,
            file_name=file_path.name,
            current_page=current_page,
            current_chapter=current_chapter,
            total_pages=total_pages,
            total_chapters=document.total_chapters,
            last_read_time=datetime.now().isoformat()
        )
        
        return progress
    
    def update_position(
        self,
        file_path: Path,
        current_page: int,
        current_chapter: int
    ) -> None:
        """
        更新阅读位置
        
        Args:
            file_path: 文档文件路径
            current_page: 当前页码
            current_chapter: 当前章节索引
        """
        progress = self.load_progress(file_path)
        
        if progress:
            progress.update_position(current_page, current_chapter)
            self.save_progress(progress)
    
    def remove_progress(self, file_path: Path) -> bool:
        """
        删除阅读进度
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            是否删除成功
        """
        file_hash = get_file_hash(file_path)
        
        # 读取现有进度数据
        data = read_json_file(self.config.progress_file)
        if not data or 'documents' not in data:
            return False
        
        # 删除匹配的记录
        original_count = len(data['documents'])
        data['documents'] = [
            doc for doc in data['documents']
            if doc.get('file_hash') != file_hash
        ]
        
        if len(data['documents']) == original_count:
            return False  # 未找到要删除的记录
        
        # 保存
        if data['documents']:
            write_json_file(self.config.progress_file, data)
        else:
            # 如果没有进度记录了，删除进度文件
            if self.config.progress_file.exists():
                self.config.progress_file.unlink()
        
        return True
    
    def get_all_progress(self) -> List[ReadingProgress]:
        """
        获取所有阅读进度
        
        Returns:
            阅读进度列表
        """
        data = read_json_file(self.config.progress_file)
        if not data or 'documents' not in data:
            return []
        
        progress_list = []
        for doc_data in data['documents']:
            try:
                progress = ReadingProgress.from_dict(doc_data)
                progress_list.append(progress)
            except (KeyError, ValueError):
                continue
        
        # 按最后阅读时间倒序排列
        progress_list.sort(key=lambda p: p.last_read_time, reverse=True)
        
        return progress_list
