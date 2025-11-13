"""数据模型模块"""

from .document import Document, Chapter
from .bookmark import Bookmark
from .progress import ReadingProgress

__all__ = ['Document', 'Chapter', 'Bookmark', 'ReadingProgress']
