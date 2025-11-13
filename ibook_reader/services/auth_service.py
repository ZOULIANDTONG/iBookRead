"""身份验证服务"""

import time
from typing import Optional, Tuple
from getpass import getpass

from ..config import Config
from ..utils.crypto import create_password_hash, verify_password


class AuthService:
    """身份验证服务"""
    
    # 最大重试次数
    MAX_RETRY_ATTEMPTS = 3
    
    # 失败后延迟时间（秒）
    RETRY_DELAY = 1
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化身份验证服务
        
        Args:
            config: 配置管理器实例
        """
        self.config = config or Config()
    
    def has_password(self) -> bool:
        """
        检查是否已设置密码
        
        Returns:
            是否已设置密码
        """
        return self.config.has_password()
    
    def setup_password(self, password: Optional[str] = None) -> bool:
        """
        设置密码（首次使用或重置后）
        
        Args:
            password: 密码，如果为None则交互式输入
            
        Returns:
            是否设置成功
        """
        if password is None:
            # 交互式输入密码
            password = getpass("请设置密码: ")
            confirm = getpass("请确认密码: ")
            
            if password != confirm:
                print("两次输入的密码不一致")
                return False
        
        if not password:
            print("密码不能为空")
            return False
        
        # 创建密码哈希
        password_hash, salt = create_password_hash(password)
        
        # 保存到配置
        self.config.set_password(password_hash, salt)
        
        return True
    
    def verify_password(self, password: Optional[str] = None, max_attempts: Optional[int] = None) -> bool:
        """
        验证密码
        
        Args:
            password: 密码，如果为None则交互式输入
            max_attempts: 最大尝试次数，默认使用MAX_RETRY_ATTEMPTS
            
        Returns:
            是否验证成功
        """
        if not self.has_password():
            return True  # 没有设置密码，直接通过
        
        max_attempts = max_attempts or self.MAX_RETRY_ATTEMPTS
        attempts = 0
        
        while attempts < max_attempts:
            if password is None:
                # 交互式输入密码
                input_password = getpass("请输入密码: ")
            else:
                input_password = password
            
            # 获取存储的密码哈希和盐值
            stored_hash, salt = self.config.get_password_info()
            
            if stored_hash is None or salt is None:
                return True  # 配置异常，允许通过
            
            # 验证密码
            if verify_password(input_password, salt, stored_hash):
                return True
            
            attempts += 1
            
            # 如果提供了密码参数，不再重试
            if password is not None:
                return False
            
            if attempts < max_attempts:
                print(f"密码错误，还剩 {max_attempts - attempts} 次机会")
                time.sleep(self.RETRY_DELAY)
            else:
                print("密码错误次数过多，退出程序")
        
        return False
    
    def reset_password(self) -> None:
        """重置密码（删除配置）"""
        self.config.reset_password()
    
    def authenticate(self) -> bool:
        """
        执行完整的身份验证流程
        
        Returns:
            是否认证成功
        """
        if not self.has_password():
            # 首次使用，需要设置密码
            print("欢迎使用iBookRead！")
            print("首次使用需要设置密码以保护您的数据")
            
            return self.setup_password()
        else:
            # 验证密码
            return self.verify_password()
    
    def change_password(self) -> bool:
        """
        修改密码
        
        Returns:
            是否修改成功
        """
        # 先验证旧密码
        if not self.verify_password():
            return False
        
        print("\n请设置新密码")
        new_password = getpass("新密码: ")
        confirm = getpass("确认新密码: ")
        
        if new_password != confirm:
            print("两次输入的密码不一致")
            return False
        
        if not new_password:
            print("密码不能为空")
            return False
        
        # 创建新密码哈希
        password_hash, salt = create_password_hash(new_password)
        
        # 保存到配置
        self.config.set_password(password_hash, salt)
        
        print("密码修改成功")
        return True
