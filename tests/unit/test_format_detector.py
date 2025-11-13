"""测试格式检测器"""

import pytest
from pathlib import Path
from ibook_reader.core.format_detector import FormatDetector


class TestFormatDetector:
    """格式检测器测试类"""
    
    def test_detect_txt_by_extension(self, tmp_path):
        """测试通过扩展名检测TXT"""
        test_file = tmp_path / 'test.txt'
        test_file.write_text('测试内容', encoding='utf-8')
        
        format_type = FormatDetector.detect(test_file)
        assert format_type == 'txt'
    
    def test_detect_markdown_by_extension(self, tmp_path):
        """测试通过扩展名检测Markdown"""
        test_file1 = tmp_path / 'test.md'
        test_file1.write_text('# 标题', encoding='utf-8')
        
        test_file2 = tmp_path / 'test.markdown'
        test_file2.write_text('# 标题', encoding='utf-8')
        
        assert FormatDetector.detect(test_file1) == 'markdown'
        assert FormatDetector.detect(test_file2) == 'markdown'
    
    def test_detect_epub_by_extension(self, tmp_path):
        """测试通过扩展名检测EPUB"""
        test_file = tmp_path / 'test.epub'
        test_file.write_bytes(b'PK\x03\x04' + b'test content')
        
        format_type = FormatDetector.detect(test_file)
        assert format_type == 'epub'
    
    def test_detect_mobi_by_extension(self, tmp_path):
        """测试通过扩展名检测MOBI"""
        for ext in ['.mobi', '.azw', '.azw3']:
            test_file = tmp_path / f'test{ext}'
            test_file.write_bytes(b'BOOKMOBI test content')
            
            format_type = FormatDetector.detect(test_file)
            assert format_type == 'mobi'
    
    def test_detect_by_magic_number_epub(self, tmp_path):
        """测试通过魔数检测EPUB"""
        test_file = tmp_path / 'unknown_file'
        test_file.write_bytes(b'PK\x03\x04' + b'test content')
        
        format_type = FormatDetector.detect(test_file)
        assert format_type == 'epub'
    
    def test_detect_by_magic_number_mobi(self, tmp_path):
        """测试通过魔数检测MOBI"""
        test_file = tmp_path / 'unknown_file'
        test_file.write_bytes(b'BOOKMOBI test content')
        
        format_type = FormatDetector.detect(test_file)
        assert format_type == 'mobi'
    
    def test_detect_unknown_as_txt(self, tmp_path):
        """测试未知格式默认为TXT"""
        test_file = tmp_path / 'unknown.xyz'
        test_file.write_text('some content', encoding='utf-8')
        
        format_type = FormatDetector.detect(test_file)
        assert format_type == 'txt'
    
    def test_detect_file_not_exist(self, tmp_path):
        """测试文件不存在"""
        test_file = tmp_path / 'not_exist.txt'
        
        with pytest.raises(FileNotFoundError):
            FormatDetector.detect(test_file)
    
    def test_is_supported(self, tmp_path):
        """测试文件是否支持"""
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('content', encoding='utf-8')
        
        assert FormatDetector.is_supported(txt_file) is True
    
    def test_is_supported_not_exist(self, tmp_path):
        """测试不存在的文件"""
        test_file = tmp_path / 'not_exist.txt'
        
        assert FormatDetector.is_supported(test_file) is False
