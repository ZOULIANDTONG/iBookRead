"""测试分页引擎"""

import pytest
from ibook_reader.core.paginator import Paginator, Page
from ibook_reader.models.document import Document, Chapter


class TestPaginator:
    """分页引擎测试类"""
    
    def test_create_paginator(self):
        """测试创建分页器"""
        chapters = [Chapter(0, "第一章", "这是第一章的内容")]
        doc = Document("测试文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        assert paginator.document == doc
        assert paginator.terminal_rows == 24
        assert paginator.terminal_cols == 80
        assert paginator.available_rows > 0
        assert paginator.available_cols > 0
    
    def test_available_rows_calculation(self):
        """测试可用行数计算"""
        chapters = [Chapter(0, "章节", "内容")]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        # 24 - 6 = 18
        assert paginator.available_rows == 18
    
    def test_available_cols_calculation(self):
        """测试可用列数计算"""
        chapters = [Chapter(0, "章节", "内容")]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        # 80 - 6 = 74
        assert paginator.available_cols == 74
    
    def test_paginate_single_page(self):
        """测试单页文档分页"""
        content = "这是一个短文档。\n只有几行内容。"
        chapters = [Chapter(0, "章节", content)]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        pages = paginator.paginate()
        
        assert len(pages) == 1
        assert pages[0].page_number == 1
        assert pages[0].chapter_index == 0
        assert "短文档" in pages[0].content
    
    def test_paginate_multiple_pages(self):
        """测试多页文档分页"""
        # 创建足够长的内容以产生多页
        content = "\n\n".join([f"这是第{i+1}段内容。" * 10 for i in range(20)])
        chapters = [Chapter(0, "长章节", content)]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        pages = paginator.paginate()
        
        # 应该产生多页
        assert len(pages) > 1
        
        # 页码应该连续
        for i, page in enumerate(pages):
            assert page.page_number == i + 1
    
    def test_paginate_multiple_chapters(self):
        """测试多章节分页"""
        chapters = [
            Chapter(0, "第一章", "第一章的内容" * 50),
            Chapter(1, "第二章", "第二章的内容" * 50),
            Chapter(2, "第三章", "第三章的内容" * 50)
        ]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        pages = paginator.paginate()
        
        # 应该至少有3页（每个章节至少一页）
        assert len(pages) >= 3
        
        # 检查章节索引
        chapter_indices = set(page.chapter_index for page in pages)
        assert 0 in chapter_indices
        assert 1 in chapter_indices
        assert 2 in chapter_indices
    
    def test_wrap_line_short(self):
        """测试短行换行"""
        chapters = [Chapter(0, "章节", "短内容")]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        wrapped = paginator._wrap_line("这是一段短文本")
        
        assert len(wrapped) == 1
        assert wrapped[0] == "这是一段短文本"
    
    def test_wrap_line_long(self):
        """测试长行换行"""
        chapters = [Chapter(0, "章节", "内容")]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=40)  # 较窄的列数
        
        # 创建超过40列宽度的文本
        long_text = "这是一段很长的文本内容" * 10
        wrapped = paginator._wrap_line(long_text)
        
        # 应该被分成多行
        assert len(wrapped) > 1
        
        # 每行宽度不应超过可用列数
        from ibook_reader.utils.text_utils import get_display_width
        for line in wrapped:
            assert get_display_width(line) <= paginator.available_cols
    
    def test_wrap_line_empty(self):
        """测试空行换行"""
        chapters = [Chapter(0, "章节", "内容")]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        wrapped = paginator._wrap_line("")
        
        assert len(wrapped) == 1
        assert wrapped[0] == ""
    
    def test_get_page(self):
        """测试获取页面"""
        content = "\n\n".join([f"段落{i}" for i in range(50)])
        chapters = [Chapter(0, "章节", content)]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        # 获取第一页
        page1 = paginator.get_page(1)
        assert page1 is not None
        assert page1.page_number == 1
        
        # 获取第二页
        page2 = paginator.get_page(2)
        if page2:  # 如果有第二页
            assert page2.page_number == 2
    
    def test_get_page_invalid(self):
        """测试获取无效页码"""
        chapters = [Chapter(0, "章节", "内容")]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        # 获取负数页码
        assert paginator.get_page(-1) is None
        
        # 获取超出范围的页码
        assert paginator.get_page(9999) is None
    
    def test_get_total_pages(self):
        """测试获取总页数"""
        content = "\n\n".join([f"段落{i}" for i in range(30)])
        chapters = [Chapter(0, "章节", content)]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        total = paginator.get_total_pages()
        
        assert total > 0
        assert isinstance(total, int)
    
    def test_get_page_by_chapter(self):
        """测试按章节获取页面"""
        chapters = [
            Chapter(0, "第一章", "第一章内容" * 20),
            Chapter(1, "第二章", "第二章内容" * 20),
        ]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        # 获取第一章的第一页
        page_ch0 = paginator.get_page_by_chapter(0)
        assert page_ch0 is not None
        assert page_ch0.chapter_index == 0
        
        # 获取第二章的第一页
        page_ch1 = paginator.get_page_by_chapter(1)
        assert page_ch1 is not None
        assert page_ch1.chapter_index == 1
    
    def test_get_page_by_chapter_invalid(self):
        """测试获取无效章节"""
        chapters = [Chapter(0, "章节", "内容")]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        # 获取不存在的章节
        assert paginator.get_page_by_chapter(-1) is None
        assert paginator.get_page_by_chapter(999) is None
    
    def test_update_terminal_size(self):
        """测试更新终端尺寸"""
        chapters = [Chapter(0, "章节", "内容" * 100)]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        
        # 记录原始分页结果
        original_pages = len(paginator.paginate())
        
        # 更新终端尺寸为更小
        paginator.update_terminal_size(20, 40)
        
        assert paginator.terminal_rows == 20
        assert paginator.terminal_cols == 40
        
        # 重新分页，页数应该改变
        new_pages = len(paginator.paginate())
        # 更小的终端应该产生更多页
        assert new_pages >= original_pages
    
    def test_find_page_position(self):
        """测试查找页面位置"""
        chapters = [
            Chapter(0, "第一章", "内容" * 50),
            Chapter(1, "第二章", "内容" * 50)
        ]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        pages = paginator.paginate()
        
        if len(pages) > 0:
            # 查找第一页的位置
            pos = paginator.find_page_position(1)
            assert pos is not None
            assert pos[0] == 0  # 第一章
    
    def test_chinese_english_mixed(self):
        """测试中英文混排分页"""
        content = "这是中文This is English混合内容\n" * 20
        chapters = [Chapter(0, "章节", content)]
        doc = Document("文档", chapters=chapters)
        
        paginator = Paginator(doc, rows=24, cols=80)
        pages = paginator.paginate()
        
        assert len(pages) > 0
        
        # 验证内容完整性
        all_content = '\n'.join(page.content for page in pages)
        assert "中文" in all_content
        assert "English" in all_content
