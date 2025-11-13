"""命令行入口模块"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich import print as rprint

from .config import Config
from .services.auth_service import AuthService
from .services.reader_service import ReaderService
from .ui.renderer import Renderer
from .ui.input_handler import InputHandler, Key


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        prog='ibook',
        description='命令行文档阅读工具 - 支持 EPUB、TXT、MOBI、Markdown 等格式'
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help='要打开的文档文件路径'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='ibook-reader 1.0.0'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清理所有数据（配置、进度、书签）'
    )
    
    parser.add_argument(
        '--reset-password',
        action='store_true',
        help='重置密码'
    )
    
    args = parser.parse_args()
    
    # 处理清理数据命令
    if args.clean:
        from .config import Config
        config = Config()
        config.clean_all_data()
        print("✓ 已清理所有数据")
        return 0
    
    # 处理重置密码命令
    if args.reset_password:
        from .config import Config
        config = Config()
        config.reset_password()
        print("✓ 已重置密码，下次启动时需要重新设置")
        return 0
    
    # 检查是否提供了文件路径
    if not args.file:
        parser.print_help()
        return 1
    
    file_path = Path(args.file)
    if not file_path.exists():
        rprint(f"[red]错误：文件不存在: {args.file}[/red]")
        return 1
    
    # 启动阅读器
    try:
        return start_reader(file_path)
    except KeyboardInterrupt:
        rprint("\n[yellow]已中断[/yellow]")
        return 0
    except Exception as e:
        rprint(f"[red]错误: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def start_reader(file_path: Path) -> int:
    """启动阅读器
    
    Args:
        file_path: 文档文件路径
        
    Returns:
        退出码
    """
    console = Console()
    
    # 1. 身份验证
    auth = AuthService()
    if not auth.verify_password():
        rprint("[red]密码验证失败，退出程序[/red]")
        return 1
    
    # 2. 创建阅读服务
    reader = ReaderService()
    
    # 3. 加载文档
    rprint(f"[cyan]正在加载文档: {file_path.name}...[/cyan]")
    if not reader.load_document(file_path):
        rprint(f"[red]无法加载文档: {file_path}[/red]")
        return 1
    
    rprint(f"[green]✓ 文档加载成功[/green]")
    if reader.document:
        rprint(f"  标题: {reader.document.title}")
        rprint(f"  章节数: {reader.document.total_chapters}")
    rprint(f"  总页数: {reader.total_pages}")
    rprint("\n[dim]按 ? 键查看帮助信息...[/dim]")
    
    import time
    time.sleep(1)  # 让用户看到信息
    
    # 4. 创建渲染器
    renderer = Renderer(console=console)
    
    # 5. 启动阅读循环
    return reading_loop(reader, renderer, console)


def reading_loop(reader: ReaderService, renderer: Renderer, console: Console) -> int:
    """阅读主循环
    
    Args:
        reader: 阅读服务
        renderer: UI渲染器
        console: 控制台对象
        
    Returns:
        退出码
    """
    input_handler = InputHandler()
    
    with input_handler:
        with Live(renderer.layout, console=console, screen=True, auto_refresh=False) as live:
            while True:
                # 渲染当前页
                page = reader.get_current_page()
                if page is None or reader.document is None:
                    break
                
                renderer.update(
                    page=page,
                    document=reader.document,
                    current_page=reader.current_page,
                    total_pages=reader.total_pages
                )
                live.refresh()
                
                # 等待用户输入
                key = input_handler.read_key()
                
                # 处理按键
                if key == Key.Q or key == Key.ESC:
                    # 退出
                    reader.save_and_exit()
                    break
                    
                elif key == Key.DOWN or key == Key.J or key == Key.SPACE:
                    # 下一页
                    if not reader.next_page():
                        show_message(renderer, "已到达文档末尾", live)
                        
                elif key == Key.UP or key == Key.K:
                    # 上一页
                    if not reader.prev_page():
                        show_message(renderer, "已到达文档开头", live)
                        
                elif key == Key.RIGHT or key == Key.L:
                    # 下一章
                    if not reader.next_chapter():
                        show_message(renderer, "已是最后一章", live)
                        
                elif key == Key.LEFT or key == Key.H:
                    # 上一章
                    if not reader.prev_chapter():
                        show_message(renderer, "已是第一章", live)
                        
                elif key == Key.G:
                    # 跳到开头或结尾（暂时只实现跳到开头）
                    reader.jump_to_start()
                    
                elif key == Key.M:
                    # 添加书签
                    bookmark = reader.add_bookmark()
                    if bookmark:
                        show_message(renderer, f"书签已添加（ID: {bookmark.id}）", live)
                    else:
                        show_message(renderer, "添加书签失败", live)
                        
                elif key == Key.B:
                    # 显示书签列表（暂未实现）
                    show_message(renderer, "书签列表功能开发中", live)
                    
                elif key == Key.QUESTION:
                    # 显示帮助
                    show_help(renderer, live)
    
    return 0


def show_message(renderer: Renderer, message: str, live: Live):
    """显示临时消息
    
    Args:
        renderer: 渲染器
        message: 消息内容
        live: Live对象
    """
    from .ui.components import MessageBox
    from rich.align import Align
    
    # 显示消息
    msg_box = MessageBox.create(message)
    renderer.layout["footer"].update(Align.center(msg_box))
    live.refresh()
    
    # 等待1秒
    import time
    time.sleep(1)


def show_help(renderer: Renderer, live: Live):
    """显示帮助信息
    
    Args:
        renderer: 渲染器
        live: Live对象
    """
    from .ui.components import HelpPanel
    
    # 显示帮助面板
    help_panel = HelpPanel.create()
    renderer.layout["content"].update(help_panel)
    live.refresh()
    
    # 等待用户按键
    input_handler = InputHandler()
    with input_handler:
        input_handler.read_key()


if __name__ == '__main__':
    sys.exit(main())
