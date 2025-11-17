"""Markdown文档解析器"""

from pathlib import Path
import re
import chardet

from .base import BaseParser
from ..models.document import Document, Chapter
from ..utils.text_utils import normalize_text


class MarkdownParser(BaseParser):
    """Markdown文档解析器"""
    
    # 尝试的编码列表
    ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin1']
    
    def parse(self) -> Document:
        """
        解析Markdown文档
        
        Returns:
            Document对象
        """
        # 读取文件内容
        content = self._read_file()
        
        # 标准化文本
        content = normalize_text(content)
        
        # 按一级标题分割章节
        chapters = self._split_chapters(content)
        
        # 如果没有章节，创建单章节
        if not chapters:
            chapters = [Chapter(
                index=0,
                title=self._get_default_title(),
                content=content,
                start_position=0
            )]
        
        # 创建文档对象
        document = Document(
            title=self._get_default_title(),
            chapters=chapters,
            metadata={
                'format': 'markdown',
                'encoding': self._detected_encoding or 'unknown'
            }
        )
        
        return document
    
    def _read_file(self) -> str:
        """
        读取文件内容，自动检测编码
        
        Returns:
            文件内容
        """
        with open(self.file_path, 'rb') as f:
            raw_data = f.read()
        
        # 使用 chardet 检测编码
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding')
        confidence = detected.get('confidence', 0)
        
        # 如果检测置信度较高，使用检测到的编码
        if encoding and confidence > 0.7:
            try:
                content = raw_data.decode(encoding)
                self._detected_encoding = encoding
                return content
            except Exception:
                pass
        
        # 否则依次尝试常用编码
        for enc in self.ENCODINGS:
            try:
                content = raw_data.decode(enc)
                self._detected_encoding = enc
                return content
            except Exception:
                continue
        
        # 最后使用 UTF-8 并忽略错误
        self._detected_encoding = 'utf-8'
        return raw_data.decode('utf-8', errors='ignore')
    
    def _split_chapters(self, content: str) -> list[Chapter]:
        """
        按一级标题分割章节

        Args:
            content: 文档内容

        Returns:
            章节列表
        """
        chapters = []

        # 匹配一级标题（# 开头，后面跟空格或标题内容）
        h1_pattern = re.compile(r'^#\s+(.+?)$', re.MULTILINE)

        # 找到所有一级标题
        matches = list(h1_pattern.finditer(content))

        if not matches:
            # 没有一级标题，返回空列表
            return []

        # 按标题分割内容
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start_pos = match.start()

            # 确定章节内容的结束位置
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            # 提取章节内容（不包含标题行）
            chapter_content = content[match.end():end_pos].strip()

            # 清理每行的前导空格（移除 Markdown 中的缩进）
            chapter_content = self._clean_indentation(chapter_content)

            # 创建章节
            chapter = Chapter(
                index=i,
                title=title,
                content=chapter_content,
                start_position=start_pos
            )
            chapters.append(chapter)

        return chapters
    
    def _clean_indentation(self, content: str) -> str:
        """
        清理内容中的前导空格/缩进，并压缩多余的空行

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            # 移除每行的前导空格
            if line.strip():
                cleaned_lines.append(line.lstrip())
                prev_empty = False
            else:
                # 压缩连续的空行：只保留一个空行
                if not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True

        # 移除末尾的空行
        while cleaned_lines and cleaned_lines[-1] == '':
            cleaned_lines.pop()

        return '\n'.join(cleaned_lines)

    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """
        判断是否可以解析该文件

        Args:
            file_path: 文件路径

        Returns:
            是否可以解析
        """
        if not file_path.exists():
            return False

        # 检查扩展名
        ext = file_path.suffix.lower()
        return ext in ['.md', '.markdown']
