"""测试业务服务层"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from ibook_reader.services.auth_service import AuthService
from ibook_reader.services.bookmark_service import BookmarkService
from ibook_reader.services.progress_service import ProgressService
from ibook_reader.services.reader_service import ReaderService
from ibook_reader.models.document import Document, Chapter
from ibook_reader.models.bookmark import Bookmark
from ibook_reader.core.paginator import Page
from ibook_reader.config import Config


class TestAuthService:
    """身份验证服务测试类"""
    
    @pytest.fixture
    def temp_config(self):
        """创建临时配置目录"""
        temp_dir = Path(tempfile.mkdtemp())
        config = Config()
        config.config_dir = temp_dir
        config.config_file = temp_dir / 'config.json'
        config.progress_file = temp_dir / 'progress.json'
        config.bookmarks_dir = temp_dir / 'bookmarks'
        config._ensure_directories()
        
        yield config
        
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    def test_create_auth_service(self, temp_config):
        """测试创建身份验证服务"""
        auth = AuthService(config=temp_config)
        
        assert auth.config == temp_config
        assert auth.MAX_RETRY_ATTEMPTS == 3
    
    def test_has_password_false(self, temp_config):
        """测试未设置密码"""
        auth = AuthService(config=temp_config)
        
        assert not auth.has_password()
    
    def test_setup_password(self, temp_config):
        """测试设置密码"""
        auth = AuthService(config=temp_config)
        
        result = auth.setup_password("test123")
        
        assert result is True
        assert auth.has_password()
    
    def test_setup_password_empty(self, temp_config):
        """测试设置空密码"""
        auth = AuthService(config=temp_config)
        
        result = auth.setup_password("")
        
        assert result is False
        assert not auth.has_password()
    
    def test_verify_password_correct(self, temp_config):
        """测试验证正确密码"""
        auth = AuthService(config=temp_config)
        auth.setup_password("test123")
        
        result = auth.verify_password("test123")
        
        assert result is True
    
    def test_verify_password_incorrect(self, temp_config):
        """测试验证错误密码"""
        auth = AuthService(config=temp_config)
        auth.setup_password("test123")
        
        result = auth.verify_password("wrong", max_attempts=1)
        
        assert result is False
    
    def test_verify_password_no_password(self, temp_config):
        """测试未设置密码时验证"""
        auth = AuthService(config=temp_config)
        
        result = auth.verify_password("any")
        
        assert result is True
    
    def test_reset_password(self, temp_config):
        """测试重置密码"""
        auth = AuthService(config=temp_config)
        auth.setup_password("test123")
        
        auth.reset_password()
        
        assert not auth.has_password()


class TestBookmarkService:
    """书签服务测试类"""
    
    @pytest.fixture
    def temp_config(self):
        """创建临时配置目录"""
        temp_dir = Path(tempfile.mkdtemp())
        config = Config()
        config.config_dir = temp_dir
        config.config_file = temp_dir / 'config.json'
        config.progress_file = temp_dir / 'progress.json'
        config.bookmarks_dir = temp_dir / 'bookmarks'
        config._ensure_directories()
        
        yield config
        
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_file = Path(tempfile.mktemp(suffix='.txt'))
        temp_file.write_text("测试内容")
        
        yield temp_file
        
        # 清理
        if temp_file.exists():
            temp_file.unlink()
    
    def test_create_bookmark_service(self, temp_config):
        """测试创建书签服务"""
        service = BookmarkService(config=temp_config)
        
        assert service.config == temp_config
        assert service.MAX_BOOKMARKS == 50
    
    def test_load_bookmarks_empty(self, temp_config, temp_file):
        """测试加载空书签列表"""
        service = BookmarkService(config=temp_config)
        
        bookmarks = service.load_bookmarks(temp_file)
        
        assert bookmarks == []
    
    def test_add_bookmark(self, temp_config, temp_file):
        """测试添加书签"""
        service = BookmarkService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        page = Page("页面内容", 1, 0)
        
        bookmark = service.add_bookmark(temp_file, page, doc)
        
        assert bookmark.id == 1
        assert bookmark.page_number == 1
        assert bookmark.chapter_index == 0
        assert bookmark.chapter_name == "第一章"
    
    def test_add_multiple_bookmarks(self, temp_config, temp_file):
        """测试添加多个书签"""
        service = BookmarkService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        page1 = Page("页面1", 1, 0)
        page2 = Page("页面2", 2, 0)
        
        bookmark1 = service.add_bookmark(temp_file, page1, doc)
        bookmark2 = service.add_bookmark(temp_file, page2, doc)
        
        assert bookmark1.id == 1
        assert bookmark2.id == 2
        
        bookmarks = service.load_bookmarks(temp_file)
        assert len(bookmarks) == 2
    
    def test_remove_bookmark(self, temp_config, temp_file):
        """测试删除书签"""
        service = BookmarkService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        page = Page("页面内容", 1, 0)
        
        bookmark = service.add_bookmark(temp_file, page, doc)
        result = service.remove_bookmark(temp_file, bookmark.id)
        
        assert result is True
        assert len(service.load_bookmarks(temp_file)) == 0
    
    def test_remove_nonexistent_bookmark(self, temp_config, temp_file):
        """测试删除不存在的书签"""
        service = BookmarkService(config=temp_config)
        
        result = service.remove_bookmark(temp_file, 999)
        
        assert result is False
    
    def test_get_bookmark(self, temp_config, temp_file):
        """测试获取书签"""
        service = BookmarkService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        page = Page("页面内容", 1, 0)
        
        added_bookmark = service.add_bookmark(temp_file, page, doc)
        retrieved_bookmark = service.get_bookmark(temp_file, added_bookmark.id)
        
        assert retrieved_bookmark is not None
        assert retrieved_bookmark.id == added_bookmark.id
    
    def test_clear_all_bookmarks(self, temp_config, temp_file):
        """测试清除所有书签"""
        service = BookmarkService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        page = Page("页面内容", 1, 0)
        
        service.add_bookmark(temp_file, page, doc)
        service.add_bookmark(temp_file, page, doc)
        
        count = service.clear_all_bookmarks(temp_file)
        
        assert count == 2
        assert len(service.load_bookmarks(temp_file)) == 0


class TestProgressService:
    """进度服务测试类"""
    
    @pytest.fixture
    def temp_config(self):
        """创建临时配置目录"""
        temp_dir = Path(tempfile.mkdtemp())
        config = Config()
        config.config_dir = temp_dir
        config.config_file = temp_dir / 'config.json'
        config.progress_file = temp_dir / 'progress.json'
        config.bookmarks_dir = temp_dir / 'bookmarks'
        config._ensure_directories()
        
        yield config
        
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        temp_file = Path(tempfile.mktemp(suffix='.txt'))
        temp_file.write_text("测试内容")
        
        yield temp_file
        
        # 清理
        if temp_file.exists():
            temp_file.unlink()
    
    def test_create_progress_service(self, temp_config):
        """测试创建进度服务"""
        service = ProgressService(config=temp_config)
        
        assert service.config == temp_config
    
    def test_load_progress_none(self, temp_config, temp_file):
        """测试加载不存在的进度"""
        service = ProgressService(config=temp_config)
        
        progress = service.load_progress(temp_file)
        
        assert progress is None
    
    def test_create_and_save_progress(self, temp_config, temp_file):
        """测试创建和保存进度"""
        service = ProgressService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        progress = service.create_progress(temp_file, doc, 5, 0, 100)
        
        assert progress.current_page == 5
        assert progress.total_pages == 100
        
        service.save_progress(progress)
        
        loaded = service.load_progress(temp_file)
        assert loaded is not None
        assert loaded.current_page == 5
    
    def test_update_position(self, temp_config, temp_file):
        """测试更新位置"""
        service = ProgressService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        progress = service.create_progress(temp_file, doc, 1, 0, 100)
        service.save_progress(progress)
        
        service.update_position(temp_file, 10, 0)
        
        loaded = service.load_progress(temp_file)
        assert loaded.current_page == 10
    
    def test_remove_progress(self, temp_config, temp_file):
        """测试删除进度"""
        service = ProgressService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        progress = service.create_progress(temp_file, doc, 1, 0, 100)
        service.save_progress(progress)
        
        result = service.remove_progress(temp_file)
        
        assert result is True
        assert service.load_progress(temp_file) is None
    
    def test_get_all_progress(self, temp_config, temp_file):
        """测试获取所有进度"""
        service = ProgressService(config=temp_config)
        
        doc = Document("测试文档", chapters=[Chapter(0, "第一章", "内容")])
        progress = service.create_progress(temp_file, doc, 1, 0, 100)
        service.save_progress(progress)
        
        all_progress = service.get_all_progress()
        
        assert len(all_progress) == 1
        assert all_progress[0].file_name == temp_file.name


class TestReaderService:
    """阅读控制服务测试类"""
    
    @pytest.fixture
    def temp_config(self):
        """创建临时配置目录"""
        temp_dir = Path(tempfile.mkdtemp())
        config = Config()
        config.config_dir = temp_dir
        config.config_file = temp_dir / 'config.json'
        config.progress_file = temp_dir / 'progress.json'
        config.bookmarks_dir = temp_dir / 'bookmarks'
        config._ensure_directories()
        
        yield config
        
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_txt_file(self):
        """创建临时TXT文件"""
        temp_file = Path(tempfile.mktemp(suffix='.txt'))
        content = "\n\n".join([f"这是第{i+1}段内容。" * 10 for i in range(20)])
        temp_file.write_text(content, encoding='utf-8')
        
        yield temp_file
        
        # 清理
        if temp_file.exists():
            temp_file.unlink()
    
    def test_create_reader_service(self):
        """测试创建阅读服务"""
        service = ReaderService()
        
        assert service.bookmark_service is not None
        assert service.progress_service is not None
        assert service.current_page == 1
    
    def test_load_document(self, temp_txt_file):
        """测试加载文档"""
        service = ReaderService()
        
        result = service.load_document(temp_txt_file, rows=24, cols=80)
        
        assert result is True
        assert service.document is not None
        assert service.paginator is not None
        assert service.total_pages > 0
    
    def test_get_current_page(self, temp_txt_file):
        """测试获取当前页面"""
        service = ReaderService()
        service.load_document(temp_txt_file, rows=24, cols=80)
        
        page = service.get_current_page()
        
        assert page is not None
        assert page.page_number == 1
    
    def test_next_page(self, temp_txt_file):
        """测试下一页"""
        service = ReaderService()
        service.load_document(temp_txt_file, rows=24, cols=80)
        
        original_page = service.current_page
        result = service.next_page()
        
        assert result is True
        assert service.current_page == original_page + 1
    
    def test_prev_page(self, temp_txt_file):
        """测试上一页"""
        service = ReaderService()
        service.load_document(temp_txt_file, rows=24, cols=80)
        service.current_page = 2
        
        result = service.prev_page()
        
        assert result is True
        assert service.current_page == 1
    
    def test_prev_page_at_start(self, temp_txt_file):
        """测试在开头时上一页"""
        service = ReaderService()
        service.load_document(temp_txt_file, rows=24, cols=80)
        
        result = service.prev_page()
        
        assert result is False
        assert service.current_page == 1
    
    def test_jump_to_page(self, temp_txt_file):
        """测试跳转到指定页"""
        service = ReaderService()
        service.load_document(temp_txt_file, rows=24, cols=80)
        
        result = service.jump_to_page(5)
        
        assert result is True
        assert service.current_page == 5
    
    def test_jump_to_start(self, temp_txt_file):
        """测试跳到开头"""
        service = ReaderService()
        service.load_document(temp_txt_file, rows=24, cols=80)
        service.current_page = 10
        
        result = service.jump_to_start()
        
        assert result is True
        assert service.current_page == 1
    
    def test_jump_to_end(self, temp_txt_file):
        """测试跳到结尾"""
        service = ReaderService()
        service.load_document(temp_txt_file, rows=24, cols=80)
        
        result = service.jump_to_end()
        
        assert result is True
        assert service.current_page == service.total_pages
