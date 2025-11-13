#!/usr/bin/env python3
"""手动测试脚本 - 测试完整的阅读流程"""

from pathlib import Path
from ibook_reader.services.reader_service import ReaderService
from ibook_reader.parsers.factory import ParserFactory


def test_epub_file():
    """测试EPUB文件"""
    print("=" * 60)
    print("测试 EPUB 文件")
    print("=" * 60)
    
    epub_file = Path(__file__).parent / 'testFile' / 'new_yorker.epub'
    if not epub_file.exists():
        print(f"❌ EPUB文件不存在: {epub_file}")
        return False
    
    # 测试解析器
    parser = ParserFactory.create_parser(epub_file)
    if parser is None:
        print(f"❌ 无法创建EPUB解析器")
        return False
    
    print(f"✓ 解析器创建成功: {parser.__class__.__name__}")
    
    # 解析文档
    try:
        document = parser.parse()
        print(f"✓ 文档解析成功")
        print(f"  - 标题: {document.title}")
        print(f"  - 作者: {document.author or '未知'}")
        print(f"  - 章节数: {document.total_chapters}")
    except Exception as e:
        print(f"❌ 文档解析失败: {e}")
        return False
    
    # 测试阅读服务
    reader = ReaderService()
    if not reader.load_document(epub_file, rows=24, cols=80):
        print(f"❌ 加载文档失败")
        return False
    
    print(f"✓ 文档加载成功")
    print(f"  - 总页数: {reader.total_pages}")
    
    # 测试翻页
    page1 = reader.get_current_page()
    if page1:
        print(f"✓ 获取第1页成功")
        print(f"  - 页码: {page1.page_number}")
        print(f"  - 内容长度: {len(page1.content)} 字符")
        print(f"  - 内容预览:\n{page1.content[:200]}...")
    
    # 测试下一页
    if reader.total_pages > 1:
        reader.next_page()
        page2 = reader.get_current_page()
        print(f"✓ 翻到第2页成功")
        print(f"  - 页码: {page2.page_number}")
    
    # 测试书签
    try:
        bookmark = reader.add_bookmark(note="测试书签")
        print(f"✓ 添加书签成功")
        print(f"  - 书签ID: {bookmark.id}")
        print(f"  - 页码: {bookmark.page_number}")
        print(f"  - 预览: {bookmark.preview_text}")
    except Exception as e:
        print(f"⚠ 添加书签失败: {e}")
    
    print("\n✅ EPUB文件测试通过！\n")
    return True


def test_mobi_file():
    """测试MOBI文件"""
    print("=" * 60)
    print("测试 MOBI 文件")
    print("=" * 60)
    
    mobi_file = Path(__file__).parent / 'testFile' / 'new_yorker.mobi'
    if not mobi_file.exists():
        print(f"❌ MOBI文件不存在: {mobi_file}")
        return False
    
    # 测试解析器
    parser = ParserFactory.create_parser(mobi_file)
    if parser is None:
        print(f"❌ 无法创建MOBI解析器")
        return False
    
    print(f"✓ 解析器创建成功: {parser.__class__.__name__}")
    
    # 解析文档
    try:
        document = parser.parse()
        print(f"✓ 文档解析成功")
        print(f"  - 标题: {document.title}")
        print(f"  - 作者: {document.author or '未知'}")
        print(f"  - 章节数: {document.total_chapters}")
    except Exception as e:
        print(f"❌ 文档解析失败: {e}")
        return False
    
    # 测试阅读服务
    reader = ReaderService()
    if not reader.load_document(mobi_file, rows=24, cols=80):
        print(f"❌ 加载文档失败")
        return False
    
    print(f"✓ 文档加载成功")
    print(f"  - 总页数: {reader.total_pages}")
    
    # 测试翻页
    page1 = reader.get_current_page()
    if page1:
        print(f"✓ 获取第1页成功")
        print(f"  - 页码: {page1.page_number}")
        print(f"  - 内容长度: {len(page1.content)} 字符")
        print(f"  - 内容预览:\n{page1.content[:200]}...")
    
    # 测试跳页
    if reader.total_pages > 10:
        reader.jump_to_page(10)
        page10 = reader.get_current_page()
        print(f"✓ 跳到第10页成功")
        print(f"  - 页码: {page10.page_number}")
    
    print("\n✅ MOBI文件测试通过！\n")
    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("iBookRead 集成测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试EPUB
    results.append(("EPUB", test_epub_file()))
    
    # 测试MOBI
    results.append(("MOBI", test_mobi_file()))
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for format_type, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{format_type:10s} - {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
