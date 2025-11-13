"""测试文档解析器"""

import pytest
from pathlib import Path
from ibook_reader.parsers import (
    TxtParser,
    MarkdownParser,
    EpubParser,
    MobiParser,
    ParserFactory
)
from ibook_reader.models.document import Document


class TestTxtParser:
    """TXT解析器测试"""
    
    def test_parse_utf8(self, tmp_path):
        """测试解析UTF-8文本"""
        test_file = tmp_path / 'test.txt'
        content = '这是一个测试文档\n第二行内容'
        test_file.write_text(content, encoding='utf-8')
        
        parser = TxtParser(test_file)
        doc = parser.parse()
        
        assert isinstance(doc, Document)
        assert doc.title == 'test'
        assert len(doc.chapters) == 1
        assert '测试文档' in doc.chapters[0].content
        assert doc.metadata['format'] == 'txt'
    
    def test_parse_gbk(self, tmp_path):
        """测试解析GBK编码文本"""
        test_file = tmp_path / 'test_gbk.txt'
        content = '这是GBK编码的文本'
        test_file.write_bytes(content.encode('gbk'))
        
        parser = TxtParser(test_file)
        doc = parser.parse()
        
        assert 'GBK编码' in doc.chapters[0].content
    
    def test_parse_with_bom(self, tmp_path):
        """测试解析带BOM的文本"""
        test_file = tmp_path / 'test_bom.txt'
        content = '\ufeff这是带BOM的文本'
        test_file.write_text(content, encoding='utf-8')
        
        parser = TxtParser(test_file)
        doc = parser.parse()
        
        # BOM应该被移除
        assert not doc.chapters[0].content.startswith('\ufeff')
        assert '带BOM的文本' in doc.chapters[0].content
    
    def test_can_parse(self, tmp_path):
        """测试能否解析"""
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('content', encoding='utf-8')
        
        md_file = tmp_path / 'test.md'
        md_file.write_text('# Title', encoding='utf-8')
        
        assert TxtParser.can_parse(txt_file) is True
        assert TxtParser.can_parse(md_file) is False
    
    def test_file_not_exist(self, tmp_path):
        """测试文件不存在"""
        test_file = tmp_path / 'not_exist.txt'
        
        with pytest.raises(FileNotFoundError):
            TxtParser(test_file)


class TestMarkdownParser:
    """Markdown解析器测试"""
    
    def test_parse_with_chapters(self, tmp_path):
        """测试解析带章节的Markdown"""
        test_file = tmp_path / 'test.md'
        content = """# 第一章
第一章的内容

# 第二章
第二章的内容

# 第三章
第三章的内容
"""
        test_file.write_text(content, encoding='utf-8')
        
        parser = MarkdownParser(test_file)
        doc = parser.parse()
        
        assert isinstance(doc, Document)
        assert len(doc.chapters) == 3
        assert doc.chapters[0].title == '第一章'
        assert doc.chapters[1].title == '第二章'
        assert doc.chapters[2].title == '第三章'
        assert '第一章的内容' in doc.chapters[0].content
        assert doc.metadata['format'] == 'markdown'
    
    def test_parse_without_chapters(self, tmp_path):
        """测试解析无章节的Markdown"""
        test_file = tmp_path / 'test.md'
        content = """这是一个没有一级标题的文档
只有普通内容
"""
        test_file.write_text(content, encoding='utf-8')
        
        parser = MarkdownParser(test_file)
        doc = parser.parse()
        
        assert len(doc.chapters) == 1
        assert doc.chapters[0].title == 'test'
        assert '普通内容' in doc.chapters[0].content
    
    def test_parse_single_chapter(self, tmp_path):
        """测试解析单章节Markdown"""
        test_file = tmp_path / 'test.md'
        content = """# 唯一的章节
这是唯一章节的内容
"""
        test_file.write_text(content, encoding='utf-8')
        
        parser = MarkdownParser(test_file)
        doc = parser.parse()
        
        assert len(doc.chapters) == 1
        assert doc.chapters[0].title == '唯一的章节'
    
    def test_can_parse(self, tmp_path):
        """测试能否解析"""
        md_file1 = tmp_path / 'test.md'
        md_file1.write_text('# Title', encoding='utf-8')
        
        md_file2 = tmp_path / 'test.markdown'
        md_file2.write_text('# Title', encoding='utf-8')
        
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('content', encoding='utf-8')
        
        assert MarkdownParser.can_parse(md_file1) is True
        assert MarkdownParser.can_parse(md_file2) is True
        assert MarkdownParser.can_parse(txt_file) is False


class TestParserFactory:
    """解析器工厂测试"""
    
    def test_create_txt_parser(self, tmp_path):
        """测试创建TXT解析器"""
        test_file = tmp_path / 'test.txt'
        test_file.write_text('content', encoding='utf-8')
        
        parser = ParserFactory.create_parser(test_file)
        
        assert parser is not None
        assert isinstance(parser, TxtParser)
    
    def test_create_markdown_parser(self, tmp_path):
        """测试创建Markdown解析器"""
        test_file = tmp_path / 'test.md'
        test_file.write_text('# Title', encoding='utf-8')
        
        parser = ParserFactory.create_parser(test_file)
        
        assert parser is not None
        assert isinstance(parser, MarkdownParser)
    
    def test_create_parser_auto_detect(self, tmp_path):
        """测试自动检测格式创建解析器"""
        # 创建没有扩展名的文件，但有EPUB魔数
        test_file = tmp_path / 'unknown_file'
        test_file.write_bytes(b'PK\x03\x04' + b'test')
        
        parser = ParserFactory.create_parser(test_file)
        
        assert parser is not None
        assert isinstance(parser, EpubParser)
    
    def test_is_supported(self, tmp_path):
        """测试文件是否支持"""
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('content', encoding='utf-8')
        
        assert ParserFactory.is_supported(txt_file) is True
    
    def test_file_not_exist(self, tmp_path):
        """测试文件不存在"""
        test_file = tmp_path / 'not_exist.txt'
        
        with pytest.raises(FileNotFoundError):
            ParserFactory.create_parser(test_file)
    
    def test_parse_complete_flow(self, tmp_path):
        """测试完整解析流程"""
        test_file = tmp_path / 'story.md'
        content = """# 序章
这是序章的内容

# 第一章
故事开始了

# 第二章
故事继续
"""
        test_file.write_text(content, encoding='utf-8')
        
        # 使用工厂创建解析器
        parser = ParserFactory.create_parser(test_file)
        assert parser is not None
        
        # 解析文档
        doc = parser.parse()
        
        # 验证结果
        assert doc.title == 'story'
        assert len(doc.chapters) == 3
        assert doc.total_chapters == 3
        assert doc.chapters[0].title == '序章'
        assert '故事开始' in doc.chapters[1].content
