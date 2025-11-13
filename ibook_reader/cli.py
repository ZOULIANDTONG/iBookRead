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
    
    parser.add_argument(
        '--ui',
        action='store_true',
        help='使用交互式UI模式（默认为纯文本模式）'
    )
    
    parser.add_argument(
        '--page',
        type=int,
        metavar='N',
        help='跳转到指定页码（仅UI模式）'
    )
    
    parser.add_argument(
        '--chapter',
        type=int,
        metavar='N',
        help='跳转到指定章节（仅UI模式）'
    )
    
    parser.add_argument(
        '--percent',
        type=float,
        metavar='N',
        help='跳转到指定百分比进度（0-100，仅UI模式）'
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
        if args.ui:
            # 构建跳转选项
            jump_options = {}
            if args.page is not None:
                jump_options['page'] = args.page
            if args.chapter is not None:
                jump_options['chapter'] = args.chapter
            if args.percent is not None:
                jump_options['percent'] = args.percent
            
            return start_reader(file_path, jump_options)
        else:
            # 纯文本模式不支持跳转
            if args.page or args.chapter or args.percent:
                rprint("[yellow]警告：跳转参数仅在 --ui 模式下有效[/yellow]")
            return plain_text_mode(file_path)
    except KeyboardInterrupt:
        rprint("\n[yellow]已中断[/yellow]")
        return 0
    except Exception as e:
        rprint(f"[red]错误: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def plain_text_mode(file_path: Path) -> int:
    """纯文本输出模式（默认模式，不需要密码验证）
    
    Args:
        file_path: 文档文件路径
        
    Returns:
        退出码
    """
    from .parsers.factory import ParserFactory
    import subprocess
    import sys
    import shutil
    
    # 1. 创建解析器
    rprint(f"[cyan]正在加载文档: {file_path.name}...[/cyan]")
    parser = ParserFactory.create_parser(file_path)
    if parser is None:
        rprint(f"[red]无法解析文档格式: {file_path}[/red]")
        return 1
    
    # 2. 解析文档
    try:
        document = parser.parse()
    except Exception as e:
        rprint(f"[red]解析文档失败: {e}[/red]")
        return 1
    
    # 3. 输出文档信息
    rprint(f"\n[green]✓ 文档加载成功[/green]")
    rprint(f"[bold cyan]标题:[/bold cyan] {document.title}")
    if document.author:
        rprint(f"[bold cyan]作者:[/bold cyan] {document.author}")
    rprint(f"[bold cyan]章节数:[/bold cyan] {document.total_chapters}")
    rprint(f"\n{'=' * 80}\n")
    
    # 4. 输出所有章节内容
    content_lines = []
    for chapter in document.chapters:
        # 章节标题
        content_lines.append(f"\n{'=' * 80}")
        content_lines.append(f"{chapter.title}")
        content_lines.append(f"{'=' * 80}\n")
        
        # 章节内容
        content_lines.append(chapter.content)
        
        # 章节分隔
        if chapter.index < document.total_chapters - 1:
            content_lines.append("")
    
    full_content = '\n'.join(content_lines)
    
    # 5. 检查是否是管道输出或重定向
    if not sys.stdout.isatty():
        # 管道或重定向，直接输出
        print(full_content)
    else:
        # 终端输出，使用分页器
        pager = shutil.which('less') or shutil.which('more')
        
        if pager:
            try:
                # 使用 less 或 more 进行分页显示
                process = subprocess.Popen(
                    [pager, '-R'],  # -R 支持颜色
                    stdin=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=full_content)
                return process.returncode or 0
            except Exception:
                # 如果分页器失败，直接输出
                print(full_content)
        else:
            # 没有分页器，直接输出
            print(full_content)
    
    rprint(f"\n[green]✓ 文档读取完成[/green]")
    return 0


def start_reader(file_path: Path, jump_options: dict = None) -> int:
    """启动阅读器
    
    Args:
        file_path: 文档文件路径
        jump_options: 跳转选项 {'page': N, 'chapter': N, 'percent': N}
        
    Returns:
        退出码
    """
    console = Console()
    jump_options = jump_options or {}
    
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
    
    # 处理跳转选项
    jump_applied = False
    if jump_options:
        if 'page' in jump_options:
            page_num = jump_options['page']
            if reader.jump_to_page(page_num):
                rprint(f"[cyan]✓ 已跳转到第 {page_num} 页[/cyan]")
                jump_applied = True
            else:
                rprint(f"[red]✗ 无效的页码: {page_num} (共 {reader.total_pages} 页)[/red]")
        
        elif 'chapter' in jump_options:
            chapter_num = jump_options['chapter']
            if reader.document and 0 <= chapter_num < reader.document.total_chapters:
                # 使用 paginator 获取章节的第一页
                if reader.paginator:
                    chapter_page = reader.paginator.get_page_by_chapter(chapter_num)
                    if chapter_page:
                        reader.jump_to_page(chapter_page.page_number)
                        rprint(f"[cyan]✓ 已跳转到第 {chapter_num} 章[/cyan]")
                        jump_applied = True
            if not jump_applied:
                total_ch = reader.document.total_chapters if reader.document else 0
                rprint(f"[red]✗ 无效的章节: {chapter_num} (共 {total_ch} 章)[/red]")
        
        elif 'percent' in jump_options:
            percent = jump_options['percent']
            if 0 <= percent <= 100:
                target_page = max(1, int(reader.total_pages * percent / 100))
                reader.jump_to_page(target_page)
                rprint(f"[cyan]✓ 已跳转到 {percent}% 进度 (第 {target_page} 页)[/cyan]")
                jump_applied = True
            else:
                rprint(f"[red]✗ 无效的百分比: {percent} (请输入 0-100)[/red]")
    
    if not jump_applied:
        rprint("\n[dim]按 ? 键查看帮助信息...[/dim]")
    
    import time
    time.sleep(1.5 if jump_applied else 1)  # 让用户看到信息
    
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
