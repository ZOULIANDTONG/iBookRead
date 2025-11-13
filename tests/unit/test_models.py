"""测试数据模型"""

import pytest
from datetime import datetime
from ibook_reader.models.document import Document, Chapter
from ibook_reader.models.bookmark import Bookmark
from ibook_reader.models.progress import ReadingProgress


class TestChapter:
    """章节模型测试"""
    
    def test_create_chapter(self):
        """测试创建章节"""
        chapter = Chapter(
            index=0,
            title="第一章",
            content="这是第一章的内容",
            start_position=0
        )
        
        assert chapter.index == 0
        assert chapter.title == "第一章"
        assert chapter.content == "这是第一章的内容"
        assert chapter.start_position == 0
    
    def test_chapter_default_title(self):
        """测试章节默认标题"""
        chapter = Chapter(index=0, title="", content="内容")
        assert chapter.title == "第 1 章"
        
        chapter2 = Chapter(index=2, title="", content="内容")
        assert chapter2.title == "第 3 章"
    
    def test_chapter_invalid_index(self):
        """测试无效的章节索引"""
        with pytest.raises(ValueError, match="章节索引不能为负数"):
            Chapter(index=-1, title="标题", content="内容")


class TestDocument:
    """文档模型测试"""
    
    def test_create_document(self):
        """测试创建文档"""
        chapters = [
            Chapter(0, "第一章", "内容1"),
            Chapter(1, "第二章", "内容2")
        ]
        
        doc = Document(
            title="测试文档",
            chapters=chapters,
            author="作者",
            language="zh-CN"
        )
        
        assert doc.title == "测试文档"
        assert doc.author == "作者"
        assert doc.language == "zh-CN"
        assert len(doc.chapters) == 2
    
    def test_document_empty_title(self):
        """测试空标题"""
        chapters = [Chapter(0, "章节", "内容")]
        
        with pytest.raises(ValueError, match="文档标题不能为空"):
            Document(title="", chapters=chapters)
    
    def test_document_empty_chapters(self):
        """测试空章节列表"""
        with pytest.raises(ValueError, match="文档必须至少包含一个章节"):
            Document(title="标题", chapters=[])
    
    def test_total_chapters(self):
        """测试获取总章节数"""
        chapters = [
            Chapter(0, "章节1", "内容1"),
            Chapter(1, "章节2", "内容2"),
            Chapter(2, "章节3", "内容3")
        ]
        doc = Document(title="文档", chapters=chapters)
        
        assert doc.total_chapters == 3
    
    def test_get_chapter(self):
        """测试获取章节"""
        chapters = [
            Chapter(0, "第一章", "内容1"),
            Chapter(1, "第二章", "内容2")
        ]
        doc = Document(title="文档", chapters=chapters)
        
        chapter = doc.get_chapter(1)
        assert chapter is not None
        assert chapter.title == "第二章"
        
        # 超出范围
        assert doc.get_chapter(5) is None
        assert doc.get_chapter(-1) is None
    
    def test_full_content(self):
        """测试获取完整内容"""
        chapters = [
            Chapter(0, "第一章", "第一章内容"),
            Chapter(1, "第二章", "第二章内容")
        ]
        doc = Document(title="文档", chapters=chapters)
        
        full = doc.full_content
        assert "第一章内容" in full
        assert "第二章内容" in full


class TestBookmark:
    """书签模型测试"""
    
    def test_create_bookmark(self):
        """测试创建书签"""
        bookmark = Bookmark(
            id=1,
            page_number=10,
            chapter_index=2,
            chapter_name="第三章",
            preview_text="这是预览文本"
        )
        
        assert bookmark.id == 1
        assert bookmark.page_number == 10
        assert bookmark.chapter_index == 2
        assert bookmark.chapter_name == "第三章"
        assert bookmark.preview_text == "这是预览文本"
    
    def test_bookmark_invalid_page(self):
        """测试无效的页码"""
        with pytest.raises(ValueError, match="页码必须大于0"):
            Bookmark(
                id=1,
                page_number=0,
                chapter_index=0,
                chapter_name="章节",
                preview_text="预览"
            )
    
    def test_bookmark_invalid_chapter(self):
        """测试无效的章节索引"""
        with pytest.raises(ValueError, match="章节索引不能为负数"):
            Bookmark(
                id=1,
                page_number=1,
                chapter_index=-1,
                chapter_name="章节",
                preview_text="预览"
            )
    
    def test_bookmark_truncate_preview(self):
        """测试预览文本截断"""
        long_text = "这是一段很长的预览文本" * 10
        bookmark = Bookmark(
            id=1,
            page_number=1,
            chapter_index=0,
            chapter_name="章节",
            preview_text=long_text
        )
        
        assert len(bookmark.preview_text) == 50
    
    def test_bookmark_to_dict(self):
        """测试转换为字典"""
        bookmark = Bookmark(
            id=1,
            page_number=5,
            chapter_index=1,
            chapter_name="第二章",
            preview_text="预览文本",
            note="备注"
        )
        
        data = bookmark.to_dict()
        
        assert data['id'] == 1
        assert data['page_number'] == 5
        assert data['chapter_index'] == 1
        assert data['chapter_name'] == "第二章"
        assert data['preview_text'] == "预览文本"
        assert data['note'] == "备注"
    
    def test_bookmark_from_dict(self):
        """测试从字典创建"""
        data = {
            'id': 2,
            'page_number': 15,
            'chapter_index': 3,
            'chapter_name': "第四章",
            'preview_text': "预览",
            'created_at': '2024-01-01T12:00:00',
            'note': None
        }
        
        bookmark = Bookmark.from_dict(data)
        
        assert bookmark.id == 2
        assert bookmark.page_number == 15
        assert bookmark.chapter_index == 3
        assert bookmark.chapter_name == "第四章"


class TestReadingProgress:
    """阅读进度模型测试"""
    
    def test_create_progress(self):
        """测试创建进度"""
        progress = ReadingProgress(
            file_path="/path/to/book.epub",
            file_hash="abc123",
            file_name="book.epub",
            current_page=10,
            current_chapter=2,
            total_pages=100,
            total_chapters=10,
            last_read_time=datetime.now().isoformat()
        )
        
        assert progress.file_path == "/path/to/book.epub"
        assert progress.file_hash == "abc123"
        assert progress.current_page == 10
        assert progress.current_chapter == 2
        assert progress.total_pages == 100
        assert progress.total_chapters == 10
        assert progress.read_percentage == 10.0
    
    def test_progress_calculate_percentage(self):
        """测试计算百分比"""
        progress = ReadingProgress(
            file_path="/path/to/book.epub",
            file_hash="abc123",
            file_name="book.epub",
            current_page=50,
            current_chapter=5,
            total_pages=200,
            total_chapters=10,
            last_read_time=datetime.now().isoformat()
        )
        
        assert progress.read_percentage == 25.0
    
    def test_progress_invalid_total_pages(self):
        """测试无效的总页数"""
        with pytest.raises(ValueError, match="总页数必须大于0"):
            ReadingProgress(
                file_path="/path",
                file_hash="hash",
                file_name="file",
                current_page=1,
                current_chapter=0,
                total_pages=0,
                total_chapters=1,
                last_read_time=datetime.now().isoformat()
            )
    
    def test_progress_invalid_total_chapters(self):
        """测试无效的总章节数"""
        with pytest.raises(ValueError, match="总章节数必须大于0"):
            ReadingProgress(
                file_path="/path",
                file_hash="hash",
                file_name="file",
                current_page=1,
                current_chapter=0,
                total_pages=10,
                total_chapters=0,
                last_read_time=datetime.now().isoformat()
            )
    
    def test_progress_update_position(self):
        """测试更新位置"""
        progress = ReadingProgress(
            file_path="/path",
            file_hash="hash",
            file_name="file",
            current_page=1,
            current_chapter=0,
            total_pages=100,
            total_chapters=10,
            last_read_time=datetime.now().isoformat()
        )
        
        # 更新到第50页，第5章
        progress.update_position(50, 5)
        
        assert progress.current_page == 50
        assert progress.current_chapter == 5
        assert progress.read_percentage == 50.0
    
    def test_progress_update_position_boundary(self):
        """测试更新位置边界处理"""
        progress = ReadingProgress(
            file_path="/path",
            file_hash="hash",
            file_name="file",
            current_page=1,
            current_chapter=0,
            total_pages=100,
            total_chapters=10,
            last_read_time=datetime.now().isoformat()
        )
        
        # 尝试设置超出范围的值
        progress.update_position(200, 20)
        
        # 应该被限制在有效范围内
        assert progress.current_page == 100
        assert progress.current_chapter == 9
        
        # 尝试设置负值
        progress.update_position(-5, -1)
        assert progress.current_page == 1
        assert progress.current_chapter == 0
    
    def test_progress_to_dict(self):
        """测试转换为字典"""
        progress = ReadingProgress(
            file_path="/path/to/book.epub",
            file_hash="abc123",
            file_name="book.epub",
            current_page=10,
            current_chapter=2,
            total_pages=100,
            total_chapters=10,
            last_read_time="2024-01-01T12:00:00"
        )
        
        data = progress.to_dict()
        
        assert data['file_path'] == "/path/to/book.epub"
        assert data['file_hash'] == "abc123"
        assert data['current_page'] == 10
        assert data['read_percentage'] == 10.0
    
    def test_progress_from_dict(self):
        """测试从字典创建"""
        data = {
            'file_path': "/path/to/book.epub",
            'file_hash': "abc123",
            'file_name': "book.epub",
            'current_page': 25,
            'current_chapter': 5,
            'total_pages': 100,
            'total_chapters': 10,
            'last_read_time': "2024-01-01T12:00:00",
            'read_percentage': 25.0
        }
        
        progress = ReadingProgress.from_dict(data)
        
        assert progress.file_path == "/path/to/book.epub"
        assert progress.current_page == 25
        assert progress.current_chapter == 5
