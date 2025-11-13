"""测试文本工具模块"""

import pytest
from ibook_reader.utils.text_utils import (
    get_char_width,
    get_display_width,
    truncate_text,
    normalize_text,
    wrap_text,
    extract_preview
)


class TestTextUtils:
    """文本工具测试类"""
    
    def test_get_char_width_ascii(self):
        """测试ASCII字符宽度"""
        assert get_char_width('a') == 1
        assert get_char_width('Z') == 1
        assert get_char_width('1') == 1
        assert get_char_width(' ') == 1
    
    def test_get_char_width_chinese(self):
        """测试中文字符宽度"""
        assert get_char_width('中') == 2
        assert get_char_width('文') == 2
        assert get_char_width('测') == 2
    
    def test_get_char_width_empty(self):
        """测试空字符"""
        assert get_char_width('') == 0
    
    def test_get_display_width_mixed(self):
        """测试混合文本宽度"""
        # "Hello中文" = 5 + 4 = 9
        assert get_display_width("Hello中文") == 9
        
        # "测试123" = 4 + 3 = 7
        assert get_display_width("测试123") == 7
        
        # 纯ASCII
        assert get_display_width("Hello") == 5
        
        # 纯中文
        assert get_display_width("你好") == 4
    
    def test_truncate_text_no_truncate(self):
        """测试不需要截断的文本"""
        text = "Hello"
        result = truncate_text(text, max_width=10)
        assert result == "Hello"
    
    def test_truncate_text_ascii(self):
        """测试截断ASCII文本"""
        text = "Hello World"
        result = truncate_text(text, max_width=8)
        # "Hello..." = 8个字符宽度
        assert result == "Hello..."
    
    def test_truncate_text_chinese(self):
        """测试截断中文文本"""
        text = "这是一个测试文本"
        # 最大宽度10，"..." 占3，所以最多7个宽度 = 3个中文字符
        result = truncate_text(text, max_width=10)
        assert result == "这是一..."
        # 结果宽度应该不超过最大宽度
        assert get_display_width(result) <= 10
    
    def test_truncate_text_mixed(self):
        """测试截断混合文本"""
        text = "测试Test文本"
        # 最大宽度10
        result = truncate_text(text, max_width=10)
        assert get_display_width(result) <= 10
    
    def test_normalize_text_crlf(self):
        """测试标准化Windows换行符"""
        text = "第一行\r\n第二行\r\n第三行"
        result = normalize_text(text)
        assert result == "第一行\n第二行\n第三行"
    
    def test_normalize_text_cr(self):
        """测试标准化Mac换行符"""
        text = "第一行\r第二行\r第三行"
        result = normalize_text(text)
        assert result == "第一行\n第二行\n第三行"
    
    def test_normalize_text_bom(self):
        """测试去除BOM"""
        text = "\ufeff这是文本内容"
        result = normalize_text(text)
        assert result == "这是文本内容"
        assert not result.startswith('\ufeff')
    
    def test_wrap_text_simple(self):
        """测试简单换行"""
        text = "Hello World"
        result = wrap_text(text, max_width=5)
        # "Hello" 和 " Worl" 和 "d"
        assert len(result) == 3
        assert all(get_display_width(line) <= 5 for line in result)
    
    def test_wrap_text_chinese(self):
        """测试中文换行"""
        text = "这是一个测试"
        result = wrap_text(text, max_width=4)
        # 每行最多2个中文字符
        assert len(result) == 3
        assert result[0] == "这是"
        assert result[1] == "一个"
        assert result[2] == "测试"
    
    def test_wrap_text_with_newline(self):
        """测试包含换行符的文本"""
        text = "第一行\n第二行"
        result = wrap_text(text, max_width=10)
        assert len(result) == 2
        assert result[0] == "第一行"
        assert result[1] == "第二行"
    
    def test_wrap_text_empty(self):
        """测试空文本"""
        result = wrap_text("", max_width=10)
        assert result == ['']
    
    def test_wrap_text_mixed(self):
        """测试混合文本换行"""
        text = "Hello中文World"
        result = wrap_text(text, max_width=8)
        # "Hello中" = 7, "文World" 超过8，需要拆分
        assert all(get_display_width(line) <= 8 for line in result)
    
    def test_extract_preview_short(self):
        """测试提取短预览"""
        text = "这是一个简短的文本"
        result = extract_preview(text, max_length=50)
        assert result == "这是一个简短的文本"
    
    def test_extract_preview_long(self):
        """测试提取长预览"""
        text = "这是一个很长的文本内容，" * 10
        result = extract_preview(text, max_length=20)
        assert len(result) == 20
    
    def test_extract_preview_with_newlines(self):
        """测试包含换行符的预览"""
        text = "第一行\n第二行\n第三行"
        result = extract_preview(text, max_length=50)
        # 换行符应该被替换为空格
        assert '\n' not in result
        assert result == "第一行 第二行 第三行"
    
    def test_extract_preview_with_spaces(self):
        """测试包含多余空格的预览"""
        text = "这是    一个   有多余   空格的文本"
        result = extract_preview(text, max_length=50)
        # 多余空格应该被合并
        assert result == "这是 一个 有多余 空格的文本"
