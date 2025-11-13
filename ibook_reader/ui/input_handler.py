"""跨平台输入处理器"""

import sys
import tty
import termios
from typing import Optional, Callable
from enum import Enum


class Key(Enum):
    """键盘按键枚举"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    ENTER = "enter"
    ESC = "esc"
    SPACE = "space"
    
    # 字母键
    J = "j"
    K = "k"
    H = "h"
    L = "l"
    G = "g"
    M = "m"
    B = "b"
    Q = "q"
    QUESTION = "?"
    D = "d"
    Y = "y"
    N = "n"
    
    # 功能键
    UNKNOWN = "unknown"


class InputHandler:
    """跨平台输入处理器"""
    
    def __init__(self):
        """初始化输入处理器"""
        self.is_windows = sys.platform.startswith('win')
        self._old_settings = None
    
    def _setup_terminal(self) -> None:
        """设置终端为原始模式（Unix/Linux/macOS）"""
        if not self.is_windows:
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
    
    def _restore_terminal(self) -> None:
        """恢复终端设置（Unix/Linux/macOS）"""
        if not self.is_windows and self._old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
    
    def read_key(self) -> Key:
        """
        读取一个按键
        
        Returns:
            Key枚举值
        """
        if self.is_windows:
            return self._read_key_windows()
        else:
            return self._read_key_unix()
    
    def _read_key_unix(self) -> Key:
        """读取按键（Unix/Linux/macOS）"""
        # 读取第一个字符
        char = sys.stdin.read(1)
        
        # 处理特殊字符
        if char == '\x1b':  # ESC序列
            # 读取下一个字符
            next_char = sys.stdin.read(1)
            
            if next_char == '':  # 单独的ESC键
                return Key.ESC
            
            if next_char == '[':  # ANSI转义序列
                third_char = sys.stdin.read(1)
                
                if third_char == 'A':
                    return Key.UP
                elif third_char == 'B':
                    return Key.DOWN
                elif third_char == 'C':
                    return Key.RIGHT
                elif third_char == 'D':
                    return Key.LEFT
        
        # 处理普通字符
        if char == '\r' or char == '\n':
            return Key.ENTER
        elif char == ' ':
            return Key.SPACE
        elif char == 'j' or char == 'J':
            return Key.J
        elif char == 'k' or char == 'K':
            return Key.K
        elif char == 'h' or char == 'H':
            return Key.H
        elif char == 'l' or char == 'L':
            return Key.L
        elif char == 'g':
            return Key.G
        elif char == 'G':
            return Key.G
        elif char == 'm' or char == 'M':
            return Key.M
        elif char == 'b' or char == 'B':
            return Key.B
        elif char == 'q' or char == 'Q':
            return Key.Q
        elif char == '?':
            return Key.QUESTION
        elif char == 'd' or char == 'D':
            return Key.D
        elif char == 'y' or char == 'Y':
            return Key.Y
        elif char == 'n' or char == 'N':
            return Key.N
        
        return Key.UNKNOWN
    
    def _read_key_windows(self) -> Key:
        """读取按键（Windows）"""
        try:
            import msvcrt
        except ImportError:
            # 如果msvcrt不可用，降级到简单输入
            char = sys.stdin.read(1)
            return self._parse_simple_char(char)
        
        # Windows使用msvcrt读取按键
        if msvcrt.kbhit():
            char = msvcrt.getch()
            
            # 处理特殊键（以\x00或\xe0开头）
            if char in (b'\x00', b'\xe0'):
                second = msvcrt.getch()
                
                if second == b'H':  # 上箭头
                    return Key.UP
                elif second == b'P':  # 下箭头
                    return Key.DOWN
                elif second == b'K':  # 左箭头
                    return Key.LEFT
                elif second == b'M':  # 右箭头
                    return Key.RIGHT
            
            # 处理普通字符
            char_str = char.decode('utf-8', errors='ignore')
            return self._parse_simple_char(char_str)
        
        return Key.UNKNOWN
    
    def _parse_simple_char(self, char: str) -> Key:
        """
        解析简单字符
        
        Args:
            char: 字符
            
        Returns:
            Key枚举值
        """
        if char == '\r' or char == '\n':
            return Key.ENTER
        elif char == ' ':
            return Key.SPACE
        elif char == '\x1b':
            return Key.ESC
        elif char.lower() == 'j':
            return Key.J
        elif char.lower() == 'k':
            return Key.K
        elif char.lower() == 'h':
            return Key.H
        elif char.lower() == 'l':
            return Key.L
        elif char == 'g' or char == 'G':
            return Key.G
        elif char.lower() == 'm':
            return Key.M
        elif char.lower() == 'b':
            return Key.B
        elif char.lower() == 'q':
            return Key.Q
        elif char == '?':
            return Key.QUESTION
        elif char.lower() == 'd':
            return Key.D
        elif char.lower() == 'y':
            return Key.Y
        elif char.lower() == 'n':
            return Key.N
        
        return Key.UNKNOWN
    
    def __enter__(self):
        """进入上下文管理器"""
        self._setup_terminal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        self._restore_terminal()
        return False
