"""终端UI渲染器"""

from typing import Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich.live import Live

from ..models.document import Document
from ..core.paginator import Page


class Renderer:
    """终端UI渲染器"""
    
    def __init__(self, console: Optional[Console] = None):
        """
        初始化渲染器
        
        Args:
            console: Rich Console对象，默认创建新实例
        """
        self.console = console or Console()
        self.layout = self._create_layout()
        self.live: Optional[Live] = None
    
    def _create_layout(self) -> Layout:
        """
        创建布局
        
        Returns:
            Layout对象
        """
        layout = Layout()
        
        # 分为三个区域：标题栏、内容区、状态栏
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="content"),
            Layout(name="footer", size=3)
        )
        
        return layout
    
    def render_header(
        self,
        doc_title: str,
        current_chapter: int,
        total_chapters: int,
        current_page: int,
        total_pages: int,
        percentage: float
    ) -> Panel:
        """
        渲染标题栏
        
        Args:
            doc_title: 文档标题
            current_chapter: 当前章节（从1开始）
            total_chapters: 总章节数
            current_page: 当前页码
            total_pages: 总页数
            percentage: 进度百分比
            
        Returns:
            Panel对象
        """
        # 截断过长的标题
        if len(doc_title) > 20:
            doc_title = doc_title[:17] + "..."
        
        header_text = (
            f"[bold cyan]{doc_title}[/bold cyan] | "
            f"第{current_chapter}/{total_chapters}章 | "
            f"第{current_page}/{total_pages}页 | "
            f"{percentage:.1f}%"
        )
        
        return Panel(
            Text.from_markup(header_text, justify="center"),
            style="bold white on blue",
            border_style="blue"
        )
    
    def render_content(self, page: Page) -> Panel:
        """
        渲染内容区
        
        Args:
            page: 页面对象
            
        Returns:
            Panel对象
        """
        return Panel(
            page.content,
            border_style="cyan",
            padding=(1, 2)
        )
    
    def render_footer(self, current_page: int, total_pages: int) -> Panel:
        """
        渲染状态栏
        
        Args:
            current_page: 当前页码
            total_pages: 总页数
            
        Returns:
            Panel对象
        """
        # 计算进度条
        progress_width = 20
        filled = int((current_page / total_pages) * progress_width)
        progress_bar = "=" * filled + ">" + " " * (progress_width - filled - 1)
        percentage = (current_page / total_pages) * 100
        
        footer_text = (
            f"[{progress_bar}] {percentage:.0f}% | "
            f"↑/↓翻页 | ←/→切章 | m书签 | b列表 | ?帮助 | q退出"
        )
        
        return Panel(
            Text.from_markup(footer_text, justify="center"),
            style="white on black",
            border_style="white"
        )
    
    def update(
        self,
        page: Page,
        document: Document,
        current_page: int,
        total_pages: int
    ) -> None:
        """
        更新整个界面
        
        Args:
            page: 当前页面
            document: 文档对象
            current_page: 当前页码
            total_pages: 总页数
        """
        # 计算当前章节
        current_chapter = page.chapter_index + 1
        total_chapters = document.total_chapters
        
        # 计算进度百分比
        percentage = (current_page / total_pages) * 100
        
        # 更新各个区域
        self.layout["header"].update(
            self.render_header(
                document.title,
                current_chapter,
                total_chapters,
                current_page,
                total_pages,
                percentage
            )
        )
        
        self.layout["content"].update(
            self.render_content(page)
        )
        
        self.layout["footer"].update(
            self.render_footer(current_page, total_pages)
        )
    
    def start_live(self) -> Live:
        """
        启动实时渲染
        
        Returns:
            Live对象
        """
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=4,
            screen=True
        )
        return self.live
    
    def stop_live(self) -> None:
        """停止实时渲染"""
        if self.live:
            self.live.stop()
            self.live = None
    
    def render_message(self, message: str, style: str = "bold yellow") -> None:
        """
        渲染临时消息
        
        Args:
            message: 消息内容
            style: 消息样式
        """
        self.console.print(f"\n[{style}]{message}[/{style}]", justify="center")
    
    def clear(self) -> None:
        """清除屏幕"""
        self.console.clear()
