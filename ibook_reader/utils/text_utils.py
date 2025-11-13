"""文本处理工具模块"""

import unicodedata
from typing import Optional


def get_char_width(char: str) -> int:
    """
    获取单个字符的显示宽度
    
    Args:
        char: 单个字符
        
    Returns:
        显示宽度（1或2）
    """
    if not char:
        return 0
    
    # 获取Unicode East Asian Width属性
    width = unicodedata.east_asian_width(char)
    
    # F(Fullwidth)和W(Wide)占2个宽度
    if width in ('F', 'W'):
        return 2
    # Na(Narrow)和H(Halfwidth)占1个宽度
    elif width in ('Na', 'H'):
        return 1
    # A(Ambiguous)在东亚环境中通常占2个宽度
    elif width == 'A':
        return 2
    # N(Neutral)占1个宽度
    else:
        return 1


def get_display_width(text: str) -> int:
    """
    计算文本的显示宽度（考虑中文字符）
    
    Args:
        text: 文本内容
        
    Returns:
        显示宽度
    """
    return sum(get_char_width(char) for char in text)


def truncate_text(text: str, max_width: int, suffix: str = '...') -> str:
    """
    按显示宽度截断文本
    
    Args:
        text: 原始文本
        max_width: 最大显示宽度
        suffix: 截断后添加的后缀
        
    Returns:
        截断后的文本
    """
    if get_display_width(text) <= max_width:
        return text
    
    suffix_width = get_display_width(suffix)
    target_width = max_width - suffix_width
    
    current_width = 0
    result = []
    
    for char in text:
        char_width = get_char_width(char)
        if current_width + char_width > target_width:
            break
        result.append(char)
        current_width += char_width
    
    return ''.join(result) + suffix


def normalize_text(text: str) -> str:
    """
    标准化文本（统一换行符、去除多余空白）
    
    Args:
        text: 原始文本
        
    Returns:
        标准化后的文本
    """
    # 统一换行符为 \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 去除BOM
    if text.startswith('\ufeff'):
        text = text[1:]
    
    return text


def wrap_text(text: str, max_width: int) -> list[str]:
    """
    按指定宽度自动换行
    
    Args:
        text: 原始文本
        max_width: 最大宽度
        
    Returns:
        换行后的文本列表
    """
    if not text:
        return ['']
    
    lines = []
    current_line = []
    current_width = 0
    
    for char in text:
        char_width = get_char_width(char)
        
        # 如果当前字符是换行符
        if char == '\n':
            lines.append(''.join(current_line))
            current_line = []
            current_width = 0
            continue
        
        # 如果添加当前字符会超出宽度
        if current_width + char_width > max_width:
            lines.append(''.join(current_line))
            current_line = [char]
            current_width = char_width
        else:
            current_line.append(char)
            current_width += char_width
    
    # 添加最后一行
    if current_line:
        lines.append(''.join(current_line))
    
    return lines if lines else ['']


def extract_preview(text: str, max_length: int = 50) -> str:
    """
    提取预览文本
    
    Args:
        text: 原始文本
        max_length: 最大字符长度
        
    Returns:
        预览文本
    """
    # 移除换行符和多余空白
    text = ' '.join(text.split())
    
    # 截断到指定长度
    if len(text) > max_length:
        return text[:max_length]
    
    return text
