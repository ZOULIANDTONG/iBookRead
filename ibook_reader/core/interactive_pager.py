"""交互式分页器 - 支持进度追踪"""

import sys
import os
import shutil
import tty
import termios
import subprocess
from typing import Optional, Callable


class InteractivePager:
    """交互式分页器，支持实时进度追踪"""

    def __init__(self, content: str, on_position_change: Optional[Callable[[int, int], None]] = None, start_line: int = 0):
        """
        初始化分页器

        Args:
            content: 要显示的完整内容（字符串）
            on_position_change: 位置改变时的回调函数，参数为 (当前行号, 总行数)
            start_line: 初始显示的行号（用于恢复进度）
        """
        self.content = content
        self.lines = content.split('\n')
        self.total_lines = len(self.lines)
        self.current_line = max(0, min(start_line, max(0, self.total_lines - 1)))
        self.on_position_change = on_position_change
        
        # 获取终端尺寸
        try:
            terminal_size = shutil.get_terminal_size()
            self.terminal_height = terminal_size.lines
            self.terminal_width = terminal_size.columns
        except:
            self.terminal_height = 24
            self.terminal_width = 80
        
        # 可显示行数（留一行给状态栏）
        self.display_lines = max(1, self.terminal_height - 1)
    
    def display_page(self):
        """显示当前页"""
        # 使用 ANSI 转义序列清屏并移动光标到左上角
        # \033[2J 清屏，\033[H 移动光标到 (0,0)
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()

        # 计算结束行
        end_line = min(self.current_line + self.display_lines, self.total_lines)

        # 显示内容
        for i in range(self.current_line, end_line):
            if i < self.total_lines:
                # 使用 write 而不是 print，确保精确控制输出
                sys.stdout.write(self.lines[i] + '\r\n')

        # 填充剩余空行（保持状态栏在底部）
        shown_lines = end_line - self.current_line
        for _ in range(self.display_lines - shown_lines):
            sys.stdout.write('\r\n')

        # 显示状态栏
        percentage = int((end_line / self.total_lines) * 100) if self.total_lines > 0 else 100
        status = f"\033[7m {self.current_line + 1}-{end_line}/{self.total_lines} ({percentage}%) | b:上一页/space:下一页 k:上一行/j:下一行 g:首/G:尾 q:退出 \033[0m"
        sys.stdout.write(status)
        sys.stdout.flush()

        # 触发回调
        if self.on_position_change:
            self.on_position_change(self.current_line, self.total_lines)
    
    def next_page(self):
        """下一页"""
        max_start = max(0, self.total_lines - self.display_lines)
        new_line = min(self.current_line + self.display_lines, max_start)
        if new_line != self.current_line:
            self.current_line = new_line
            return True
        return False
    
    def prev_page(self):
        """上一页"""
        new_line = max(0, self.current_line - self.display_lines)
        if new_line != self.current_line:
            self.current_line = new_line
            return True
        return False
    
    def next_line(self):
        """下一行"""
        max_start = max(0, self.total_lines - self.display_lines)
        if self.current_line < max_start:
            self.current_line += 1
            return True
        return False
    
    def prev_line(self):
        """上一行"""
        if self.current_line > 0:
            self.current_line -= 1
            return True
        return False
    
    def goto_start(self):
        """跳到开头"""
        if self.current_line != 0:
            self.current_line = 0
            return True
        return False
    
    def goto_end(self):
        """跳到结尾"""
        max_start = max(0, self.total_lines - self.display_lines)
        if self.current_line != max_start:
            self.current_line = max_start
            return True
        return False
    
    def run(self) -> int:
        """
        运行分页器
        
        Returns:
            最终的行号位置
        """
        if not sys.stdin.isatty():
            # 非终端模式，直接打印所有内容
            print(self.content)
            return 0
        
        # 保存终端设置
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # 启用 alternate screen buffer（备用屏幕缓冲区）
            # 这样退出时会自动恢复到之前的屏幕状态，就像 vim/less 一样
            sys.stdout.write('\033[?1049h')
            sys.stdout.flush()

            # 设置为原始模式
            tty.setraw(fd)

            # 显示第一页
            self.display_page()
            
            while True:
                # 读取按键
                ch = sys.stdin.read(1)

                changed = False

                # 处理按键
                if ch == 'q' or ch == 'Q':
                    break
                elif ch == ' ' or ch == 'f':  # 空格或f: 下一页
                    changed = self.next_page()
                elif ch == 'b':  # b: 上一页
                    changed = self.prev_page()
                elif ch == 'j' or ch == '\r':  # j或回车: 下一行
                    changed = self.next_line()
                elif ch == 'k':  # k: 上一行
                    changed = self.prev_line()
                elif ch == 'g':  # g: 跳到开头
                    changed = self.goto_start()
                elif ch == 'G':  # G: 跳到结尾
                    changed = self.goto_end()
                elif ch == '\x03':  # Ctrl+C
                    break

                # 只在内容改变时重新显示
                if changed:
                    self.display_page()

        finally:
            # 禁用 alternate screen buffer，恢复到之前的屏幕状态
            sys.stdout.write('\033[?1049l')
            sys.stdout.flush()

            # 恢复终端设置
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return self.current_line
