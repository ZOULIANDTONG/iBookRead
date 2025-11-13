"""加密工具模块"""

import hashlib
import os
from typing import Tuple


def generate_salt(length: int = 16) -> str:
    """
    生成随机盐值
    
    Args:
        length: 盐值字节长度，默认16字节
        
    Returns:
        十六进制格式的盐值字符串
    """
    return os.urandom(length).hex()


def hash_password(password: str, salt: str) -> str:
    """
    使用SHA-256算法对密码进行哈希
    
    Args:
        password: 原始密码
        salt: 盐值
        
    Returns:
        十六进制格式的哈希值
    """
    if not password:
        raise ValueError("密码不能为空")
    if not salt:
        raise ValueError("盐值不能为空")
    
    # 将密码和盐值组合后进行哈希
    combined = (password + salt).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """
    验证密码是否正确
    
    Args:
        password: 待验证的密码
        salt: 盐值
        stored_hash: 存储的哈希值
        
    Returns:
        密码是否匹配
    """
    try:
        computed_hash = hash_password(password, salt)
        return computed_hash == stored_hash
    except Exception:
        return False


def create_password_hash(password: str) -> Tuple[str, str]:
    """
    创建密码哈希和盐值
    
    Args:
        password: 原始密码
        
    Returns:
        (哈希值, 盐值) 元组
    """
    salt = generate_salt()
    password_hash = hash_password(password, salt)
    return password_hash, salt
