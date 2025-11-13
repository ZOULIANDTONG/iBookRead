"""测试文件工具模块"""

import pytest
import tempfile
import json
from pathlib import Path
from ibook_reader.utils.file_utils import (
    get_config_dir,
    ensure_dir,
    atomic_write,
    get_file_hash,
    read_json_file,
    write_json_file,
    get_file_size,
    is_large_file
)


class TestFileUtils:
    """文件工具测试类"""
    
    def test_get_config_dir(self):
        """测试获取配置目录"""
        config_dir = get_config_dir()
        
        assert isinstance(config_dir, Path)
        assert config_dir.name == '.ibook_reader'
        assert config_dir.parent == Path.home()
    
    def test_ensure_dir(self, tmp_path):
        """测试确保目录存在"""
        test_dir = tmp_path / 'test_dir' / 'sub_dir'
        
        # 目录不存在
        assert not test_dir.exists()
        
        # 创建目录
        ensure_dir(test_dir)
        
        # 目录应该存在
        assert test_dir.exists()
        assert test_dir.is_dir()
        
        # 再次调用不应该抛出异常
        ensure_dir(test_dir)
    
    def test_atomic_write(self, tmp_path):
        """测试原子写入"""
        test_file = tmp_path / 'test.txt'
        content = "测试内容\n第二行"
        
        # 写入文件
        atomic_write(test_file, content, backup=False)
        
        # 验证文件内容
        assert test_file.exists()
        assert test_file.read_text(encoding='utf-8') == content
    
    def test_atomic_write_with_backup(self, tmp_path):
        """测试带备份的原子写入"""
        test_file = tmp_path / 'test.txt'
        backup_file = tmp_path / 'test.txt.bak'
        
        # 创建原始文件
        original_content = "原始内容"
        test_file.write_text(original_content, encoding='utf-8')
        
        # 更新文件
        new_content = "新内容"
        atomic_write(test_file, new_content, backup=True)
        
        # 验证新内容
        assert test_file.read_text(encoding='utf-8') == new_content
        
        # 验证备份文件
        assert backup_file.exists()
        assert backup_file.read_text(encoding='utf-8') == original_content
    
    def test_get_file_hash(self, tmp_path):
        """测试计算文件哈希"""
        test_file = tmp_path / 'test.txt'
        content = "测试内容123"
        test_file.write_text(content, encoding='utf-8')
        
        # 计算哈希
        file_hash = get_file_hash(test_file)
        
        # 哈希应该是32个字符的十六进制字符串（MD5）
        assert len(file_hash) == 32
        assert all(c in '0123456789abcdef' for c in file_hash.lower())
        
        # 相同内容应该产生相同的哈希
        file_hash2 = get_file_hash(test_file)
        assert file_hash == file_hash2
    
    def test_get_file_hash_different_content(self, tmp_path):
        """测试不同内容产生不同哈希"""
        file1 = tmp_path / 'file1.txt'
        file2 = tmp_path / 'file2.txt'
        
        file1.write_text("内容1", encoding='utf-8')
        file2.write_text("内容2", encoding='utf-8')
        
        hash1 = get_file_hash(file1)
        hash2 = get_file_hash(file2)
        
        assert hash1 != hash2
    
    def test_get_file_hash_not_found(self, tmp_path):
        """测试文件不存在时抛出异常"""
        test_file = tmp_path / 'not_exist.txt'
        
        with pytest.raises(FileNotFoundError):
            get_file_hash(test_file)
    
    def test_read_json_file(self, tmp_path):
        """测试读取JSON文件"""
        test_file = tmp_path / 'test.json'
        data = {'name': '测试', 'value': 123, 'list': [1, 2, 3]}
        
        # 写入JSON
        test_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        
        # 读取JSON
        result = read_json_file(test_file)
        
        assert result == data
    
    def test_read_json_file_not_exist(self, tmp_path):
        """测试读取不存在的JSON文件"""
        test_file = tmp_path / 'not_exist.json'
        
        # 应该返回默认值
        result = read_json_file(test_file, default={'default': True})
        
        assert result == {'default': True}
    
    def test_read_json_file_invalid(self, tmp_path):
        """测试读取无效的JSON文件"""
        test_file = tmp_path / 'invalid.json'
        test_file.write_text("这不是有效的JSON", encoding='utf-8')
        
        # 应该返回默认值
        result = read_json_file(test_file, default=None)
        
        assert result is None
    
    def test_write_json_file(self, tmp_path):
        """测试写入JSON文件"""
        test_file = tmp_path / 'test.json'
        data = {
            'title': '测试文档',
            'count': 100,
            'items': ['项目1', '项目2']
        }
        
        # 写入JSON
        write_json_file(test_file, data, backup=False)
        
        # 验证文件内容
        assert test_file.exists()
        loaded_data = json.loads(test_file.read_text(encoding='utf-8'))
        assert loaded_data == data
    
    def test_get_file_size(self, tmp_path):
        """测试获取文件大小"""
        test_file = tmp_path / 'test.txt'
        content = "测试内容" * 100
        test_file.write_text(content, encoding='utf-8')
        
        size = get_file_size(test_file)
        
        assert size > 0
        assert size == test_file.stat().st_size
    
    def test_get_file_size_not_found(self, tmp_path):
        """测试获取不存在文件的大小"""
        test_file = tmp_path / 'not_exist.txt'
        
        with pytest.raises(FileNotFoundError):
            get_file_size(test_file)
    
    def test_is_large_file(self, tmp_path):
        """测试判断大文件"""
        # 创建小文件
        small_file = tmp_path / 'small.txt'
        small_file.write_text("小文件", encoding='utf-8')
        
        # 应该不是大文件
        assert is_large_file(small_file, threshold_mb=1) is False
        
        # 创建较大文件（2MB）
        large_file = tmp_path / 'large.txt'
        large_content = "x" * (2 * 1024 * 1024)
        large_file.write_text(large_content, encoding='utf-8')
        
        # 应该是大文件
        assert is_large_file(large_file, threshold_mb=1) is True
        assert is_large_file(large_file, threshold_mb=5) is False
