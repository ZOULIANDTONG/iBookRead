"""命令行入口模块"""

import argparse
import sys
import subprocess
import shutil
import signal
from pathlib import Path
from typing import Optional

from .config import Config
from .services.auth_service import AuthService
from .services.reader_service import ReaderService
from .parsers.factory import ParserFactory

# 忽略 SIGPIPE 信号，避免管道关闭时的错误
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


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
        version='ibook-reader 2.0.0'
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
        '--set-password',
        action='store_true',
        help='设置或修改密码'
    )

    parser.add_argument(
        '--page',
        type=int,
        metavar='N',
        help='从指定页码开始输出'
    )

    parser.add_argument(
        '--chapter',
        type=int,
        metavar='N',
        help='从指定章节开始输出'
    )

    parser.add_argument(
        '--percent',
        type=float,
        metavar='N',
        help='从指定百分比进度开始输出（0-100）'
    )

    parser.add_argument(
        '--pages',
        type=int,
        metavar='N',
        help='输出指定数量的页数（配合跳转参数使用）'
    )

    args = parser.parse_args()

    # 处理清理数据命令
    if args.clean:
        config = Config()
        config.clean_all_data()
        print("✓ 已清理所有数据")
        return 0

    # 处理重置密码命令
    if args.reset_password:
        config = Config()
        config.reset_password()
        print("✓ 已重置密码，下次启动时需要重新设置")
        return 0

    # 处理设置密码命令
    if args.set_password:
        config = Config()
        auth = AuthService()
        
        # 如果已有密码，先验证
        if config.has_password():
            print("当前已设置密码，需要先验证身份")
            if not auth.verify_password():
                print("✗ 密码验证失败，无法修改密码", file=sys.stderr)
                return 1
        
        # 设置新密码
        if auth.setup_password():
            print("✓ 密码设置成功")
            return 0
        else:
            print("✗ 密码设置失败", file=sys.stderr)
            return 1

    # 检查是否提供了文件路径
    if not args.file:
        parser.print_help()
        return 1

    file_path = Path(args.file).resolve()  # 转换为绝对路径
    if not file_path.exists():
        print(f"错误：文件不存在: {args.file}", file=sys.stderr)
        return 1

    # 构建跳转选项
    jump_options = {}
    if args.page is not None:
        jump_options['page'] = args.page
    if args.chapter is not None:
        jump_options['chapter'] = args.chapter
    if args.percent is not None:
        jump_options['percent'] = args.percent
    if args.pages is not None:
        jump_options['pages'] = args.pages

    # 启动阅读器
    try:
        return start_reader(file_path, jump_options)
    except KeyboardInterrupt:
        print("\n已中断", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def start_reader(file_path: Path, jump_options: dict = None) -> int:
    """启动阅读器

    Args:
        file_path: 文档文件路径
        jump_options: 跳转选项 {'page': N, 'chapter': N, 'percent': N, 'pages': N}

    Returns:
        退出码
    """
    jump_options = jump_options or {}

    # 1. 身份验证（管道输出时也需要验证）
    auth = AuthService()
    if not auth.verify_password():
        print("密码验证失败，退出程序", file=sys.stderr)
        return 1

    # 2. 加载文档（静默模式，仅在出错时显示信息）
    # print(f"正在加载文档: {file_path.name}...", file=sys.stderr)

    # 创建解析器
    doc_parser = ParserFactory.create_parser(file_path)
    if doc_parser is None:
        print(f"错误：无法解析文档格式: {file_path}", file=sys.stderr)
        return 1

    # 解析文档
    try:
        document = doc_parser.parse()
    except Exception as e:
        print(f"错误：解析文档失败: {e}", file=sys.stderr)
        return 1

    # 成功加载后不显示任何信息
    # print(f"✓ 文档加载成功", file=sys.stderr)
    # print(f"  标题: {document.title}", file=sys.stderr)
    # if document.author:
    #     print(f"  作者: {document.author}", file=sys.stderr)
    # print(f"  章节数: {document.total_chapters}", file=sys.stderr)

    # 3. 处理跳转和输出
    if jump_options:
        # 有跳转参数，使用分页模式（跳转参数优先于保存的进度）
        return output_with_jump(document, file_path, jump_options)
    else:
        # 无跳转参数，检查是否有保存的进度
        from .services.progress_service import ProgressService
        progress_service = ProgressService()
        saved_progress = progress_service.load_progress(file_path)

        if saved_progress and saved_progress.current_page > 1:
            # 有保存的进度，加载完整文档但从上次位置开始
            return output_full_document_with_resume(document, file_path, saved_progress.current_page)
        else:
            # 没有进度或从第一页开始，输出全部内容
            return output_full_document(document, file_path)


def output_full_document(document, file_path: Path = None) -> int:
    """输出完整文档

    Args:
        document: 文档对象
        file_path: 文件路径（用于保存进度）

    Returns:
        退出码
    """
    return output_full_document_with_resume(document, file_path, start_page=1)


def output_full_document_with_resume(document, file_path: Path, start_page: int = 1) -> int:
    """输出完整文档，支持从指定页码恢复

    Args:
        document: 文档对象
        file_path: 文件路径（用于保存进度）
        start_page: 起始页码（用于恢复进度时滚动到该位置）

    Returns:
        退出码
    """
    from .core.paginator import Paginator

    # 创建分页器
    paginator = Paginator(document)
    all_pages = paginator.paginate()
    total_pages = len(all_pages)

    # 验证起始页码
    if start_page < 1 or start_page > total_pages:
        start_page = 1

    # 构建完整内容（所有页面）
    content_parts = []
    page_start_lines = []  # 记录每页的起始行号
    current_line_count = 0
    prev_chapter_index = -1

    for page in all_pages:
        page_start_lines.append(current_line_count)

        # 输出章节标题
        if page.chapter_index != prev_chapter_index:
            chapter = document.get_chapter(page.chapter_index)
            if chapter:
                if content_parts:
                    content_parts.append("")
                    current_line_count += 1
                content_parts.append(chapter.title)
                content_parts.append("")
                current_line_count += 2
            prev_chapter_index = page.chapter_index

        # 输出页面内容
        content_parts.append(page.content)
        current_line_count += page.content.count('\n') + 1

    full_content = '\n'.join(content_parts)

    # 计算恢复位置的起始行
    if start_page > 1 and start_page <= len(page_start_lines):
        resume_line = page_start_lines[start_page - 1]
    else:
        resume_line = 0

    # 检查是否是管道输出或重定向
    if not sys.stdout.isatty():
        # 管道或重定向，直接输出全部内容
        print(full_content)

        # 保存进度（管道模式保存最后一页）
        if file_path:
            try:
                from .services.progress_service import ProgressService
                progress_service = ProgressService()
                last_chapter = all_pages[-1].chapter_index if all_pages else 0
                progress = progress_service.create_progress(
                    file_path, document, total_pages, last_chapter, total_pages
                )
                progress_service.save_progress(progress)
            except Exception:
                pass
    else:
        # 终端输出，使用交互式分页器
        from .core.interactive_pager import InteractivePager
        from .services.progress_service import ProgressService

        # 运行分页器，从恢复位置开始
        pager = InteractivePager(full_content, start_line=resume_line)
        final_line = pager.run()

        # 退出时保存进度
        if file_path:
            try:
                progress_service = ProgressService()

                # 根据最终行号找到对应的页码
                estimated_page = 1
                for i, line_start in enumerate(page_start_lines):
                    if final_line >= line_start:
                        estimated_page = i + 1
                    else:
                        break

                # 找到对应的章节
                if estimated_page > 0 and estimated_page <= len(all_pages):
                    estimated_chapter = all_pages[estimated_page - 1].chapter_index
                else:
                    estimated_chapter = 0

                progress = progress_service.create_progress(
                    file_path, document, estimated_page, estimated_chapter, total_pages
                )
                progress_service.save_progress(progress)
            except Exception:
                pass

    return 0


def output_with_jump(document, file_path: Path, jump_options: dict) -> int:
    """使用跳转参数输出文档

    Args:
        document: 文档对象
        file_path: 文件路径
        jump_options: 跳转选项

    Returns:
        退出码
    """
    from .core.paginator import Paginator

    # 创建分页器
    paginator = Paginator(document)
    all_pages = paginator.paginate()
    total_pages = len(all_pages)

    # 处理跳转，计算起始页码
    start_page = 1
    if 'page' in jump_options:
        page_num = jump_options['page']
        if 1 <= page_num <= total_pages:
            start_page = page_num
        else:
            print(f"✗ 错误：无效的页码: {page_num} (共 {total_pages} 页)", file=sys.stderr)
            return 1

    elif 'chapter' in jump_options:
        chapter_num = jump_options['chapter']
        if 0 <= chapter_num < document.total_chapters:
            chapter_page = paginator.get_page_by_chapter(chapter_num)
            if chapter_page:
                start_page = chapter_page.page_number
            else:
                print(f"✗ 错误：无法跳转到章节: {chapter_num}", file=sys.stderr)
                return 1
        else:
            print(f"✗ 错误：无效的章节: {chapter_num} (共 {document.total_chapters} 章)", file=sys.stderr)
            return 1

    elif 'percent' in jump_options:
        percent = jump_options['percent']
        if 0 <= percent <= 100:
            start_page = max(1, int(total_pages * percent / 100))
            if start_page == 0:
                start_page = 1
        else:
            print(f"✗ 错误：无效的百分比: {percent} (请输入 0-100)", file=sys.stderr)
            return 1

    # 检查是否使用管道或重定向
    if sys.stdout.isatty():
        # 终端模式：加载完整文档，跳转到指定位置
        return output_full_document_with_resume(document, file_path, start_page)
    else:
        # 管道模式：只输出从起始页到末尾（或指定页数）的内容
        if 'pages' in jump_options:
            end_page = min(start_page + jump_options['pages'] - 1, total_pages)
        else:
            end_page = total_pages

        prev_chapter_index = -1
        try:
            for page_num in range(start_page, end_page + 1):
                if page_num < 1 or page_num > len(all_pages):
                    continue

                page = all_pages[page_num - 1]

                # 输出章节标题
                if page.chapter_index != prev_chapter_index:
                    chapter = document.get_chapter(page.chapter_index)
                    if chapter:
                        if prev_chapter_index != -1:
                            print()
                        print(chapter.title)
                        print()
                    prev_chapter_index = page.chapter_index

                # 输出页面内容
                print(page.content)
        except BrokenPipeError:
            pass

        # 保存进度
        try:
            from .services.progress_service import ProgressService
            progress_service = ProgressService()

            if end_page > 0 and end_page <= len(all_pages):
                end_chapter = all_pages[end_page - 1].chapter_index
            else:
                end_chapter = 0

            progress = progress_service.create_progress(
                file_path, document, end_page, end_chapter, total_pages
            )
            progress_service.save_progress(progress)
        except Exception:
            pass

    return 0


def _output_with_jump_pipe_mode(document, file_path: Path, jump_options: dict) -> int:
    """管道模式下的跳转输出（保留旧逻辑用于兼容）"""
    from .core.paginator import Paginator

    paginator = Paginator(document)
    all_pages = paginator.paginate()
    total_pages = len(all_pages)

    start_page = jump_options.get('page', 1)
    if 'pages' in jump_options:
        end_page = min(start_page + jump_options['pages'] - 1, total_pages)
    else:
        end_page = total_pages

    prev_chapter_index = -1
    try:
        for page_num in range(start_page, end_page + 1):
            if page_num < 1 or page_num > len(all_pages):
                continue

            page = all_pages[page_num - 1]

            if page.chapter_index != prev_chapter_index:
                chapter = document.get_chapter(page.chapter_index)
                if chapter:
                    if prev_chapter_index != -1:
                        print()
                    print(chapter.title)
                    print()
                prev_chapter_index = page.chapter_index

            print(page.content)
    except BrokenPipeError:
        pass


if __name__ == '__main__':
    sys.exit(main())
