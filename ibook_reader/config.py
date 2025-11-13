"""配置管理模块"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .utils.file_utils import (
    get_config_dir,
    ensure_dir,
    read_json_file,
    write_json_file
)


class Config:
    """配置管理器"""
    
    VERSION = "1.0"
    
    def __init__(self):
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / 'config.json'
        self.progress_file = self.config_dir / 'progress.json'
        self.bookmarks_dir = self.config_dir / 'bookmarks'
        self.log_file = self.config_dir / 'app.log'
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        ensure_dir(self.config_dir)
        ensure_dir(self.bookmarks_dir)
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        default_config = {
            'version': self.VERSION,
            'password_hash': None,
            'salt': None,
            'created_at': None,
            'updated_at': None
        }
        
        config = read_json_file(self.config_file, default=default_config)
        
        # 确保版本字段存在
        if 'version' not in config:
            config['version'] = self.VERSION
        
        return config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """
        保存配置文件
        
        Args:
            config: 配置字典
        """
        config['version'] = self.VERSION
        config['updated_at'] = datetime.now().isoformat()
        write_json_file(self.config_file, config)
    
    def has_password(self) -> bool:
        """
        检查是否已设置密码
        
        Returns:
            是否已设置密码
        """
        config = self.load_config()
        return config.get('password_hash') is not None and config.get('salt') is not None
    
    def get_password_info(self) -> tuple[Optional[str], Optional[str]]:
        """
        获取密码哈希和盐值
        
        Returns:
            (password_hash, salt) 元组
        """
        config = self.load_config()
        return config.get('password_hash'), config.get('salt')
    
    def set_password(self, password_hash: str, salt: str) -> None:
        """
        设置密码
        
        Args:
            password_hash: 密码哈希值
            salt: 盐值
        """
        config = self.load_config()
        config['password_hash'] = password_hash
        config['salt'] = salt
        
        # 如果是首次设置，记录创建时间
        if config.get('created_at') is None:
            config['created_at'] = datetime.now().isoformat()
        
        self.save_config(config)
    
    def reset_password(self) -> None:
        """重置密码（删除配置文件）"""
        if self.config_file.exists():
            self.config_file.unlink()
    
    def get_bookmark_file(self, file_hash: str) -> Path:
        """
        获取书签文件路径
        
        Args:
            file_hash: 文件哈希值
            
        Returns:
            书签文件路径
        """
        return self.bookmarks_dir / f"{file_hash}.json"
    
    def clean_old_data(self, days: int = 30) -> int:
        """
        清理旧数据
        
        Args:
            days: 保留最近多少天的数据
            
        Returns:
            清理的记录数
        """
        from datetime import timedelta
        
        cleaned_count = 0
        threshold = datetime.now() - timedelta(days=days)
        
        # 清理进度文件
        progress_data = read_json_file(self.progress_file)
        if progress_data and 'documents' in progress_data:
            original_count = len(progress_data['documents'])
            progress_data['documents'] = [
                doc for doc in progress_data['documents']
                if datetime.fromisoformat(doc['last_read_time']) > threshold
            ]
            cleaned_count += original_count - len(progress_data['documents'])
            
            if progress_data['documents']:
                write_json_file(self.progress_file, progress_data)
            elif self.progress_file.exists():
                self.progress_file.unlink()
        
        # 清理无效的书签文件
        if self.bookmarks_dir.exists():
            for bookmark_file in self.bookmarks_dir.glob('*.json'):
                bookmark_data = read_json_file(bookmark_file)
                if bookmark_data:
                    file_path = Path(bookmark_data.get('file_path', ''))
                    # 如果原文件不存在或书签列表为空，删除书签文件
                    if not file_path.exists() or not bookmark_data.get('bookmarks'):
                        bookmark_file.unlink()
                        cleaned_count += 1
        
        return cleaned_count
    
    def clean_all_data(self) -> None:
        """清理所有数据"""
        import shutil
        
        if self.config_dir.exists():
            shutil.rmtree(self.config_dir)
        
        # 重新创建目录
        self._ensure_directories()
