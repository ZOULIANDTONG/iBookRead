"""测试配置管理模块"""

import pytest
from pathlib import Path
from ibook_reader.config import Config
from ibook_reader.utils.crypto import create_password_hash


class TestConfig:
    """配置管理器测试"""
    
    @pytest.fixture
    def temp_config(self, tmp_path, monkeypatch):
        """创建临时配置"""
        # 修改配置目录为临时目录
        test_dir = tmp_path / '.ibook_reader_test'
        monkeypatch.setattr(
            'ibook_reader.utils.file_utils.get_config_dir',
            lambda: test_dir
        )
        config = Config()
        # 确保是全新的配置目录
        if config.config_file.exists():
            config.config_file.unlink()
        return config
    
    def test_init_config(self, temp_config):
        """测试初始化配置"""
        assert temp_config.config_dir.exists()
        assert temp_config.bookmarks_dir.exists()
    
    def test_load_default_config(self, temp_config):
        """测试加载默认配置"""
        config = temp_config.load_config()
        
        assert config['version'] == "1.0"
        assert config['password_hash'] is None
        assert config['salt'] is None
    
    def test_save_and_load_config(self, temp_config):
        """测试保存和加载配置"""
        config_data = {
            'password_hash': 'test_hash',
            'salt': 'test_salt',
            'custom_field': 'custom_value'
        }
        
        temp_config.save_config(config_data)
        loaded_config = temp_config.load_config()
        
        assert loaded_config['password_hash'] == 'test_hash'
        assert loaded_config['salt'] == 'test_salt'
        assert loaded_config['custom_field'] == 'custom_value'
        assert loaded_config['version'] == "1.0"
        assert 'updated_at' in loaded_config
    
    def test_has_password_false(self, temp_config):
        """测试未设置密码"""
        assert temp_config.has_password() is False
    
    def test_has_password_true(self, temp_config):
        """测试已设置密码"""
        password_hash, salt = create_password_hash("test_password")
        temp_config.set_password(password_hash, salt)
        
        assert temp_config.has_password() is True
    
    def test_get_password_info(self, temp_config):
        """测试获取密码信息"""
        password_hash, salt = create_password_hash("my_password")
        temp_config.set_password(password_hash, salt)
        
        loaded_hash, loaded_salt = temp_config.get_password_info()
        
        assert loaded_hash == password_hash
        assert loaded_salt == salt
    
    def test_set_password(self, temp_config):
        """测试设置密码"""
        password_hash, salt = create_password_hash("secure_password")
        temp_config.set_password(password_hash, salt)
        
        config = temp_config.load_config()
        
        assert config['password_hash'] == password_hash
        assert config['salt'] == salt
        assert config['created_at'] is not None
    
    def test_reset_password(self, temp_config):
        """测试重置密码"""
        # 先设置密码
        password_hash, salt = create_password_hash("password")
        temp_config.set_password(password_hash, salt)
        assert temp_config.has_password() is True
        
        # 重置密码
        temp_config.reset_password()
        assert temp_config.has_password() is False
        assert not temp_config.config_file.exists()
    
    def test_get_bookmark_file(self, temp_config):
        """测试获取书签文件路径"""
        file_hash = "abc123def456"
        bookmark_file = temp_config.get_bookmark_file(file_hash)
        
        assert bookmark_file.parent == temp_config.bookmarks_dir
        assert bookmark_file.name == f"{file_hash}.json"
    
    def test_clean_all_data(self, temp_config):
        """测试清理所有数据"""
        # 创建一些数据
        password_hash, salt = create_password_hash("password")
        temp_config.set_password(password_hash, salt)
        
        # 创建书签文件
        bookmark_file = temp_config.get_bookmark_file("test_hash")
        bookmark_file.write_text('{"bookmarks": []}', encoding='utf-8')
        
        # 清理所有数据
        temp_config.clean_all_data()
        
        # 目录应该被重新创建但是为空
        assert temp_config.config_dir.exists()
        assert temp_config.bookmarks_dir.exists()
        assert not temp_config.config_file.exists()
        assert not bookmark_file.exists()
