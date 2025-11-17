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
        '--no-password',
        action='store_true',
        help='跳过密码验证（用于脚本或管道）'
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

    # 检查是否提供了文件路径
    if not args.file:
        parser.print_help()
        return 1

    file_path = Path(args.file)
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
        return start_reader(file_path, jump_options, args.no_password)
    except KeyboardInterrupt:
        print("\n已中断", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def start_reader(file_path: Path, jump_options: dict = None, no_password: bool = False) -> int:
    """启动阅读器

    Args:
        file_path: 文档文件路径
        jump_options: 跳转选项 {'page': N, 'chapter': N, 'percent': N, 'pages': N}
        no_password: 是否跳过密码验证

    Returns:
        退出码
    """
    jump_options = jump_options or {}

    # 1. 身份验证（除非明确跳过或输出被重定向）
    if not no_password and sys.stdout.isatty():
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
        # 有跳转参数，使用分页模式
        return output_with_jump(document, file_path, jump_options)
    else:
        # 无跳转参数，输出全部内容
        return output_full_document(document)


def output_full_document(document) -> int:
    """输出完整文档

    Args:
        document: 文档对象

    Returns:
        退出码
    """
    # 不显示分隔线
    # print(f"\n{'=' * 80}\n", file=sys.stderr)

    # 构建所有内容
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

    # 检查是否是管道输出或重定向
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

    # 不显示完成信息
    # print(f"\n✓ 文档读取完成", file=sys.stderr)
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
    # 创建阅读服务和分页器
    reader = ReaderService()

    # 手动设置文档（不通过load_document，因为那会加载进度）
    reader.document = document
    reader.file_path = file_path

    from .core.paginator import Paginator
    reader.paginator = Paginator(document)
    reader.total_pages = reader.paginator.get_total_pages()
    reader.current_page = 1

    # 不显示详细信息
    # print(f"  总页数: {reader.total_pages}", file=sys.stderr)

    # 处理跳转
    start_page = 1
    if 'page' in jump_options:
        page_num = jump_options['page']
        if 1 <= page_num <= reader.total_pages:
            start_page = page_num
            # 不显示跳转信息
            # print(f"✓ 跳转到第 {page_num} 页", file=sys.stderr)
        else:
            print(f"✗ 错误：无效的页码: {page_num} (共 {reader.total_pages} 页)", file=sys.stderr)
            return 1

    elif 'chapter' in jump_options:
        chapter_num = jump_options['chapter']
        if 0 <= chapter_num < document.total_chapters:
            chapter_page = reader.paginator.get_page_by_chapter(chapter_num)
            if chapter_page:
                start_page = chapter_page.page_number
                # 不显示跳转信息
                # print(f"✓ 跳转到第 {chapter_num} 章", file=sys.stderr)
            else:
                print(f"✗ 错误：无法跳转到章节: {chapter_num}", file=sys.stderr)
                return 1
        else:
            print(f"✗ 错误：无效的章节: {chapter_num} (共 {document.total_chapters} 章)", file=sys.stderr)
            return 1

    elif 'percent' in jump_options:
        percent = jump_options['percent']
        if 0 <= percent <= 100:
            start_page = max(1, int(reader.total_pages * percent / 100))
            # 不显示跳转信息
            # print(f"✓ 跳转到 {percent}% 进度 (第 {start_page} 页)", file=sys.stderr)
        else:
            print(f"✗ 错误：无效的百分比: {percent} (请输入 0-100)", file=sys.stderr)
            return 1

    # 确定输出的页数 - 默认输出到文档末尾
    if 'pages' in jump_options:
        # 如果明确指定了页数，只输出指定数量
        pages_to_output = jump_options['pages']
        end_page = min(start_page + pages_to_output - 1, reader.total_pages)
    else:
        # 否则输出从起始页到文档末尾的所有内容
        end_page = reader.total_pages

    # 不显示输出范围
    # print(f"  输出范围: 第 {start_page} 页 到 第 {end_page} 页 (共 {end_page - start_page + 1} 页)\n", file=sys.stderr)
    # print(f"{'=' * 80}\n", file=sys.stderr)

    # 批量获取所有页面（优化性能）
    all_pages = reader.paginator.paginate()
    
    # 检查是否使用管道或重定向（流式输出）
    use_pager = sys.stdout.isatty()
    
    if use_pager:
        # 终端输出，使用分页器，需要先构建完整内容
        content_lines = []
        prev_chapter_index = -1
        
        for page_num in range(start_page, end_page + 1):
            if page_num < 1 or page_num > len(all_pages):
                continue
                
            page = all_pages[page_num - 1]
            
            if page.chapter_index != prev_chapter_index:
                chapter = document.get_chapter(page.chapter_index)
                if chapter:
                    if content_lines:
                        content_lines.append("")
                    content_lines.append(f"{'=' * 80}")
                    content_lines.append(f"{chapter.title}")
                    content_lines.append(f"{'=' * 80}")
                    content_lines.append("")
                prev_chapter_index = page.chapter_index

            content_lines.append(page.content)

            if page_num < end_page and page_num < len(all_pages):
                next_page = all_pages[page_num]
                if next_page.chapter_index == page.chapter_index:
                    content_lines.append(f"\n{'-' * 80}")
                    content_lines.append(f"第 {page_num} 页 / 共 {reader.total_pages} 页")
                    content_lines.append(f"{'-' * 80}\n")
        
        output_content = '\n'.join(content_lines)
        
        # 使用分页器
        pager = shutil.which('less') or shutil.which('more')
        if pager:
            try:
                process = subprocess.Popen(
                    [pager, '-R'],
                    stdin=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=output_content)
                return process.returncode or 0
            except Exception:
                print(output_content)
        else:
            print(output_content)
    else:
        # 管道或重定向，流式输出（避免占用大量内存）
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
                        if prev_chapter_index != -1:  # 不是第一个章节
                            print()  # 空行分隔
                        print(f"{'=' * 80}")
                        print(f"{chapter.title}")
                        print(f"{'=' * 80}")
                        print()
                    prev_chapter_index = page.chapter_index

                # 输出页面内容
                print(page.content)

                # 输出页面分隔符
                if page_num < end_page and page_num < len(all_pages):
                    next_page = all_pages[page_num]
                    if next_page.chapter_index == page.chapter_index:
                        print(f"\n{'-' * 80}")
                        print(f"第 {page_num} 页 / 共 {reader.total_pages} 页")
                        print(f"{'-' * 80}\n")
        except BrokenPipeError:
            # 管道关闭是正常的（例如 head 命令），静默忽略
            pass

    # 不显示完成信息
    # print(f"\n✓ 内容输出完成", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
