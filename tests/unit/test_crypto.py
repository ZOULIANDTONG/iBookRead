"""测试加密工具模块"""

import pytest
from ibook_reader.utils.crypto import (
    generate_salt,
    hash_password,
    verify_password,
    create_password_hash
)


class TestCrypto:
    """加密工具测试类"""
    
    def test_generate_salt(self):
        """测试生成盐值"""
        salt1 = generate_salt()
        salt2 = generate_salt()
        
        # 盐值应该是32个字符的十六进制字符串（16字节）
        assert len(salt1) == 32
        assert len(salt2) == 32
        
        # 两次生成的盐值应该不同
        assert salt1 != salt2
        
        # 应该只包含十六进制字符
        assert all(c in '0123456789abcdef' for c in salt1.lower())
    
    def test_generate_salt_custom_length(self):
        """测试自定义长度的盐值"""
        salt = generate_salt(length=8)
        assert len(salt) == 16  # 8字节 = 16个十六进制字符
    
    def test_hash_password(self):
        """测试密码哈希"""
        password = "test_password_123"
        salt = generate_salt()
        
        hash1 = hash_password(password, salt)
        hash2 = hash_password(password, salt)
        
        # 相同密码和盐值应该产生相同的哈希
        assert hash1 == hash2
        
        # 哈希值应该是64个字符（SHA-256）
        assert len(hash1) == 64
    
    def test_hash_password_different_salt(self):
        """测试不同盐值产生不同哈希"""
        password = "test_password_123"
        salt1 = generate_salt()
        salt2 = generate_salt()
        
        hash1 = hash_password(password, salt1)
        hash2 = hash_password(password, salt2)
        
        # 不同盐值应该产生不同的哈希
        assert hash1 != hash2
    
    def test_hash_password_empty_password(self):
        """测试空密码应该抛出异常"""
        salt = generate_salt()
        
        with pytest.raises(ValueError, match="密码不能为空"):
            hash_password("", salt)
    
    def test_hash_password_empty_salt(self):
        """测试空盐值应该抛出异常"""
        with pytest.raises(ValueError, match="盐值不能为空"):
            hash_password("test_password", "")
    
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "my_secure_password"
        salt = generate_salt()
        stored_hash = hash_password(password, salt)
        
        # 验证应该成功
        assert verify_password(password, salt, stored_hash) is True
    
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "correct_password"
        wrong_password = "wrong_password"
        salt = generate_salt()
        stored_hash = hash_password(password, salt)
        
        # 验证应该失败
        assert verify_password(wrong_password, salt, stored_hash) is False
    
    def test_verify_password_wrong_salt(self):
        """测试错误盐值验证"""
        password = "test_password"
        salt1 = generate_salt()
        salt2 = generate_salt()
        stored_hash = hash_password(password, salt1)
        
        # 使用错误的盐值验证应该失败
        assert verify_password(password, salt2, stored_hash) is False
    
    def test_create_password_hash(self):
        """测试创建密码哈希和盐值"""
        password = "test_password_123"
        
        hash1, salt1 = create_password_hash(password)
        hash2, salt2 = create_password_hash(password)
        
        # 每次创建应该产生不同的盐值和哈希
        assert salt1 != salt2
        assert hash1 != hash2
        
        # 但是验证应该成功
        assert verify_password(password, salt1, hash1) is True
        assert verify_password(password, salt2, hash2) is True
    
    def test_chinese_password(self):
        """测试中文密码"""
        password = "我的密码123"
        salt = generate_salt()
        
        password_hash = hash_password(password, salt)
        
        # 验证应该成功
        assert verify_password(password, salt, password_hash) is True
        
        # 错误的中文密码应该验证失败
        assert verify_password("错误密码123", salt, password_hash) is False
