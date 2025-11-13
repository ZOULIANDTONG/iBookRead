"""命令行入口模块"""

import argparse
import sys
from pathlib import Path


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
        print(f"错误：文件不存在: {args.file}", file=sys.stderr)
        return 1
    
    print(f"正在加载文档: {file_path.name}")
    print("提示：核心功能尚未实现，请等待后续开发")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
