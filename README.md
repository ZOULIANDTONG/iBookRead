# iBookRead

<div align="center">

📚 一个轻量级、功能强大的命令行文档阅读工具

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/yourusername/iBookRead)

支持 EPUB、MOBI、TXT、Markdown 等多种文档格式

</div>

---

## ✨ 特性

- 📖 **多格式支持** - 支持 EPUB、MOBI、TXT、Markdown 等常见文档格式
- 📤 **纯文本输出** - 默认直接输出全文，方便管道处理和脚本集成
- 📄 **智能分页** - 内置交互式分页器，支持 vim 风格导航
- 🎯 **精准定位** - 支持按页码、章节、百分比跳转，可查看完整文档
- 💾 **进度保存** - 自动保存阅读进度，下次打开自动恢复
- 🔒 **密码保护** - 可选的密码保护功能，保护隐私
- 🌏 **中英文支持** - 完美支持中英文混排和多种编码
- 🚀 **高性能** - 优化的分页算法，大文档秒开
- 🔇 **静默模式** - 无干扰输出，退出分页器后屏幕干净

---

## 📦 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/iBookRead.git
cd iBookRead

# 安装
pip install .
```

---

## 🚀 快速开始

### 首次使用

**基本阅读**：

```bash
$ ibook book.epub
# 使用内置交互式分页器
# 底部显示：1-20/1000 (2%) | b:上一页/space:下一页 k:上一行/j:下一行 g:首/G:尾 q:退出
# 退出时自动保存进度
```

**再次打开（自动恢复进度）**：

```bash
$ ibook book.epub
# 自动从上次阅读位置继续
# 可以向前/向后翻页查看任意内容
```

---

## ⌨️ 分页器快捷键

在终端中阅读时，iBookRead 使用内置分页器，**支持实时进度追踪**。以下是常用快捷键：

| 按键 | 功能 | 说明 |
|-----|------|------|
| `Space` / `f` | 下一页 | 向下翻一整页 |
| `b` | 上一页 | 向上翻一整页 |
| `j` / `Enter` | 下一行 | 向下滚动一行 |
| `k` | 上一行 | 向上滚动一行 |
| `g` | 跳到开头 | 跳转到文档开头 |
| `G` | 跳到结尾 | 跳转到文档结尾 |
| `q` | 退出 | 退出阅读（自动保存实际进度） |

> **实时进度追踪**：分页器会记录您的每次翻页操作，退出时自动保存实际阅读位置！

---

## 🔧 命令行选项

```bash
ibook [选项] [文件路径]
```

### 选项说明

| 选项 | 说明 |
|-----|------|
| `-h`, `--help` | 显示帮助信息 |
| `--version` | 显示版本号 |
| `--set-password` | 设置或修改密码（已有密码需先验证） |
| `--reset-password` | 重置密码（清除现有密码） |
| `--page N` | 从指定页码开始输出到末尾 |
| `--chapter N` | 从指定章节开始输出到末尾（章节从0开始计数） |
| `--percent N` | 从指定百分比进度开始输出到末尾（0-100） |
| `--pages N` | 跳转到指定页码 |
| `--clean` | 清理所有数据（配置、进度、书签） |

### 使用示例

```bash
# 查看版本
ibook --version

# 查看帮助
ibook --help

# 阅读整本书
ibook book.epub

# 从第10章开始读到末尾（章节从0开始）
ibook --chapter 10 book.epub

# 从第100页开始读到末尾
ibook --page 100 book.epub

# 从50%进度开始读到末尾
ibook --percent 50 book.epub

# 设置或修改密码
ibook --set-password

# 重置密码（清除现有密码）
ibook --reset-password

# 清理所有数据
ibook --clean
```

---

## ⚠️ 特殊字符文件名处理

如果文件名包含中文括号 `（）`、`【】` 等特殊字符，在 **zsh** 中可能会遇到 `no matches found` 错误。这是因为 zsh 会将这些字符当作 glob 模式解析。

### 解决方案 1：使用引号（临时）

每次使用时用引号包裹文件名：

```bash
ibook "学习笔记【完整版】.txt"
```

### 解决方案 2：配置 alias（永久推荐）

在 `~/.zshrc` 文件中添加以下配置：

```bash
# 让 ibook 命令不进行 glob 扩展
alias ibook='noglob ibook'
```

然后重新加载配置：

```bash
source ~/.zshrc
```

之后就可以直接使用，无需引号：

```bash
ibook 学习笔记【完整版】.txt
```

> **注意**：Bash 用户通常不会遇到此问题，可以忽略这一节。

---

## 📁 数据存储

所有配置数据存储在用户目录下：

```
~/.ibook_reader/
├── config.json          # 配置文件（密码哈希等）
└── progress.json        # 阅读进度（按文件哈希索引）

```

- **Linux/macOS**: `~/.ibook_reader/`
- **Windows**: `%USERPROFILE%\.ibook_reader\`

### 进度文件示例

```json
{
  "documents": [{
    "file_path": "/path/to/book.epub",
    "file_hash": "468e3ee38544e1e278264097e81a866e",
    "current_page": 100,
    "current_chapter": 5,
    "total_pages": 520,
    "read_percentage": 19.2,
    "last_read_time": "2024-11-17T20:00:00"
  }]
}
```

**特性**：
- 使用绝对路径存储，任意目录访问都能匹配
- 按文件哈希索引，移动文件后进度仍然保留
- 自动清理30天未读的旧进度记录

---

## 🔒 安全性

### 密码保护

iBookRead 使用 **SHA-256** 算法加密存储密码：

- 密码经过哈希处理，不以明文存储
- 每个密码都有唯一的随机盐值
- 密码验证失败3次后自动退出
- 支持随时重置密码

### 隐私保护

- 所有数据都存储在本地
- 不会收集或上传任何用户数据
- 可随时使用 `--clean` 清理所有数据

---

## 🎯 支持的文件格式

| 格式 | 扩展名 | 支持程度 | 说明 |
|-----|-------|---------|------|
| **EPUB** | `.epub` | ✅ 完全支持 | 提取文本内容，支持章节导航 |
| **MOBI** | `.mobi`, `.azw` | ✅ 完全支持 | 提取文本内容 |
| **TXT** | `.txt` | ✅ 完全支持 | 自动检测编码（UTF-8/GBK/GB2312等） |
| **Markdown** | `.md`, `.markdown` | ✅ 完全支持 | 按一级标题分章节 |


---

## 🔮 未来计划

- [ ] PDF 格式支持

---

<div align="center">

**如果觉得有用，请给个 ⭐️ 支持一下！**

Made with ❤️ by iBookRead Team

</div>
