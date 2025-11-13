"""UI组件模块"""

from typing import List
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..models.bookmark import Bookmark


class HelpPanel:
    """帮助面板组件"""
    
    @staticmethod
    def create() -> Panel:
        """
        创建帮助面板
        
        Returns:
            Panel对象
        """
        help_table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        help_table.add_column("按键", style="yellow", width=15)
        help_table.add_column("功能", style="white")
        
        # 添加快捷键说明
        help_table.add_row("↓ / j / Space", "下一页")
        help_table.add_row("↑ / k", "上一页")
        help_table.add_row("→ / l", "下一章")
        help_table.add_row("← / h", "上一章")
        help_table.add_row("g", "跳到开头")
        help_table.add_row("G", "跳到结尾")
        help_table.add_row("m", "添加书签")
        help_table.add_row("b", "书签列表")
        help_table.add_row("?", "显示帮助")
        help_table.add_row("q / ESC", "退出阅读")
        
        return Panel(
            help_table,
            title="[bold cyan]快捷键帮助[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )


class BookmarkList:
    """书签列表组件"""
    
    @staticmethod
    def create(bookmarks: List[Bookmark], selected_index: int = 0) -> Panel:
        """
        创建书签列表
        
        Args:
            bookmarks: 书签列表
            selected_index: 选中的书签索引
            
        Returns:
            Panel对象
        """
        if not bookmarks:
            empty_text = Text(
                "暂无书签\n\n按 m 键添加书签\n按 ESC 键返回",
                style="dim",
                justify="center"
            )
            return Panel(
                empty_text,
                title="[bold cyan]书签列表[/bold cyan]",
                border_style="cyan",
                padding=(2, 2)
            )
        
        # 创建书签表格
        table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("序号", style="yellow", width=6)
        table.add_column("章节", style="green", width=20)
        table.add_column("页码", style="blue", width=8)
        table.add_column("预览", style="white")
        
        # 添加书签行
        for i, bookmark in enumerate(bookmarks):
            # 截断章节名
            chapter_name = bookmark.chapter_name
            if len(chapter_name) > 18:
                chapter_name = chapter_name[:15] + "..."
            
            # 截断预览文本
            preview = bookmark.preview_text
            if len(preview) > 30:
                preview = preview[:27] + "..."
            
            # 高亮选中行
            if i == selected_index:
                style = "bold white on blue"
                table.add_row(
                    f"► {i + 1}",
                    chapter_name,
                    str(bookmark.page_number),
                    preview,
                    style=style
                )
            else:
                table.add_row(
                    f"  {i + 1}",
                    chapter_name,
                    str(bookmark.page_number),
                    preview
                )
        
        # 添加提示信息
        hint_text = Text("\n↑/↓ 选择 | Enter 跳转 | d 删除 | ESC 返回", style="dim", justify="center")
        
        return Panel(
            table,
            title="[bold cyan]书签列表[/bold cyan]",
            subtitle=hint_text,
            border_style="cyan",
            padding=(1, 2)
        )


class MessageBox:
    """消息框组件"""
    
    @staticmethod
    def create(message: str, style: str = "yellow") -> Panel:
        """
        创建消息框
        
        Args:
            message: 消息内容
            style: 样式
            
        Returns:
            Panel对象
        """
        return Panel(
            Text(message, style=style, justify="center"),
            border_style=style,
            padding=(1, 2)
        )
    
    @staticmethod
    def create_confirm(question: str) -> Panel:
        """
        创建确认对话框
        
        Args:
            question: 问题文本
            
        Returns:
            Panel对象
        """
        text = Text(justify="center")
        text.append(question + "\n\n", style="bold white")
        text.append("y = 确认  |  n = 取消", style="dim")
        
        return Panel(
            text,
            title="[bold yellow]确认[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
