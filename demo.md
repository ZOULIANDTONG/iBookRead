# 第一章 iBookRead 简介

iBookRead 是一个强大的命令行文档阅读工具，支持多种文档格式。

它的主要特点包括：
- 支持 EPUB、MOBI、TXT、Markdown 格式
- 纯文本输出，方便管道处理
- 智能分页显示
- 密码保护功能

# 第二章 快速上手

使用 iBookRead 非常简单：

1. 安装完成后，直接运行 `ibook 文件名` 即可
2. 使用 `--no-password` 参数可以跳过密码验证
3. 使用 `--page N` 可以从指定页开始阅读
4. 使用 `--chapter N` 可以从指定章节开始

# 第三章 高级功能

## 3.1 章节跳转

你可以使用 `--chapter` 参数直接跳转到指定章节。
章节编号从 0 开始计数。

## 3.2 页码跳转

使用 `--page` 参数可以跳转到指定页码。
配合 `--pages` 参数可以控制输出的页数。

## 3.3 管道操作

iBookRead 支持管道操作，例如：
- `ibook --no-password 文档.epub | grep "关键词"`
- `ibook --no-password 文档.txt > 输出.txt`

# 第四章 总结

iBookRead 让命令行阅读变得简单高效！

希望你喜欢这个工具 😊
