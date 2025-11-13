"""文件操作工具模块"""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional


def get_config_dir() -> Path:
    """
    获取配置目录路径
    
    Returns:
        配置目录的Path对象
    """
    home = Path.home()
    config_dir = home / '.ibook_reader'
    return config_dir


def ensure_dir(path: Path) -> None:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        # 设置目录权限为700（仅用户可访问）
        try:
            os.chmod(path, 0o700)
        except Exception:
            # Windows系统可能不支持chmod
            pass


def atomic_write(file_path: Path, content: str, backup: bool = True) -> None:
    """
    原子写入文件（先写入临时文件，再重命名）
    
    Args:
        file_path: 目标文件路径
        content: 要写入的内容
        backup: 是否备份原文件
    """
    # 确保父目录存在
    ensure_dir(file_path.parent)
    
    # 如果需要备份且原文件存在
    if backup and file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        shutil.copy2(file_path, backup_path)
    
    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix='.tmp_',
        suffix=file_path.suffix
    )
    
    try:
        # 写入临时文件
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 原子替换
        shutil.move(temp_path, file_path)
    except Exception:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def get_file_hash(file_path: Path) -> str:
    """
    计算文件的MD5哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        MD5哈希值（十六进制字符串）
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    md5_hash = hashlib.md5()
    
    # 分块读取大文件
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()


def read_json_file(file_path: Path, default: Any = None) -> Any:
    """
    读取JSON文件
    
    Args:
        file_path: 文件路径
        default: 文件不存在或读取失败时的默认值
        
    Returns:
        解析后的JSON数据
    """
    if not file_path.exists():
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def write_json_file(file_path: Path, data: Any, backup: bool = True) -> None:
    """
    写入JSON文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        backup: 是否备份原文件
    """
    content = json.dumps(data, ensure_ascii=False, indent=2)
    atomic_write(file_path, content, backup=backup)


def get_file_size(file_path: Path) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    return file_path.stat().st_size


def is_large_file(file_path: Path, threshold_mb: int = 100) -> bool:
    """
    判断是否为大文件
    
    Args:
        file_path: 文件路径
        threshold_mb: 大小阈值（MB），默认100MB
        
    Returns:
        是否为大文件
    """
    size_bytes = get_file_size(file_path)
    threshold_bytes = threshold_mb * 1024 * 1024
    return size_bytes > threshold_bytes
