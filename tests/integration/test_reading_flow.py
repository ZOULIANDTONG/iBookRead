"""集成测试 - 完整阅读流程"""

import pytest
from pathlib import Path
import tempfile
import shutil

from ibook_reader.services.reader_service import ReaderService
from ibook_reader.services.auth_service import AuthService
from ibook_reader.config import Config


class TestReadingFlow:
    """阅读流程集成测试"""
    
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
    def epub_file(self):
        """获取EPUB测试文件"""
        file_path = Path(__file__).parent.parent.parent / 'testFile' / 'new_yorker.epub'
        if file_path.exists():
            return file_path
        pytest.skip("EPUB测试文件不存在")
    
    @pytest.fixture
    def mobi_file(self):
        """获取MOBI测试文件"""
        file_path = Path(__file__).parent.parent.parent / 'testFile' / 'new_yorker.mobi'
        if file_path.exists():
            return file_path
        pytest.skip("MOBI测试文件不存在")
    
    def test_load_epub_file(self, epub_file):
        """测试加载EPUB文件"""
        reader = ReaderService()
        
        result = reader.load_document(epub_file, rows=24, cols=80)
        
        assert result is True
        assert reader.document is not None
        assert reader.document.title
        assert reader.total_pages > 0
        print(f"\n✓ EPUB文件加载成功")
        print(f"  文档标题: {reader.document.title}")
        print(f"  总章节数: {reader.document.total_chapters}")
        print(f"  总页数: {reader.total_pages}")
    
    def test_load_mobi_file(self, mobi_file):
        """测试加载MOBI文件"""
        reader = ReaderService()
        
        result = reader.load_document(mobi_file, rows=24, cols=80)
        
        assert result is True
        assert reader.document is not None
        assert reader.document.title
        assert reader.total_pages > 0
        print(f"\n✓ MOBI文件加载成功")
        print(f"  文档标题: {reader.document.title}")
        print(f"  总章节数: {reader.document.total_chapters}")
        print(f"  总页数: {reader.total_pages}")
    
    def test_epub_navigation(self, epub_file, temp_config):
        """测试EPUB文件导航"""
        reader = ReaderService()
        reader.progress_service.config = temp_config
        reader.load_document(epub_file, rows=24, cols=80)
        
        # 测试获取当前页
        page1 = reader.get_current_page()
        assert page1 is not None
        assert page1.page_number == 1
        print(f"\n✓ 当前页码: {page1.page_number}")
        
        # 测试下一页
        if reader.total_pages > 1:
            result = reader.next_page()
            assert result is True
            assert reader.current_page == 2
            print(f"✓ 翻页成功，当前页: {reader.current_page}")
        
        # 测试跳到开头
        reader.jump_to_start()
        assert reader.current_page == 1
        print(f"✓ 跳到开头成功")
        
        # 测试跳到结尾
        reader.jump_to_end()
        assert reader.current_page == reader.total_pages
        print(f"✓ 跳到结尾成功，总页数: {reader.total_pages}")
    
    def test_bookmark_operations(self, epub_file, temp_config):
        """测试书签操作"""
        reader = ReaderService()
        reader.bookmark_service.config = temp_config
        reader.progress_service.config = temp_config  # 也设置进度服务的config
        reader.load_document(epub_file, rows=24, cols=80)
        
        # 添加书签
        bookmark = reader.add_bookmark(note="测试书签")
        assert bookmark is not None
        assert bookmark.id == 1
        print(f"\n✓ 添加书签成功，ID: {bookmark.id}")
        
        # 加载书签列表
        bookmarks = reader.bookmark_service.load_bookmarks(epub_file)
        assert len(bookmarks) == 1
        print(f"✓ 书签列表加载成功，共 {len(bookmarks)} 个书签")
        
        # 跳转到书签
        reader.jump_to_page(5)
        result = reader.jump_to_bookmark(bookmark.id)
        assert result is True
        assert reader.current_page == bookmark.page_number
        print(f"✓ 跳转到书签成功，页码: {reader.current_page}")
    
    def test_progress_save_and_restore(self, epub_file, temp_config):
        """测试进度保存和恢复"""
        # 第一次阅读
        reader1 = ReaderService()
        reader1.progress_service.config = temp_config
        reader1.load_document(epub_file, rows=24, cols=80)
        
        # 跳到第2页（保证不超过总页数）
        target_page = min(2, reader1.total_pages)
        reader1.jump_to_page(target_page)
        reader1.save_and_exit()
        print(f"\n✓ 进度已保存，页码: {reader1.current_page}")
        
        # 第二次打开，恢复进度
        reader2 = ReaderService()
        reader2.progress_service.config = temp_config
        reader2.load_document(epub_file, rows=24, cols=80)
        
        assert reader2.current_page == target_page
        print(f"✓ 进度恢复成功，页码: {reader2.current_page}")
