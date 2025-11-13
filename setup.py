"""安装配置文件"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_file = Path(__file__).parent / 'README.md'
long_description = ''
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

setup(
    name='ibook-reader',
    version='1.0.0',
    author='iBookRead Team',
    author_email='',
    description='命令行文档阅读工具，支持 EPUB、TXT、MOBI、Markdown 等格式',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/iBookRead',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    install_requires=[
        'rich>=13.0.0',
        'ebooklib>=0.18',
        'mobi>=0.3.0',
        'markdown>=3.4.0',
        'chardet>=5.0.0',
        'beautifulsoup4>=4.11.0',
        'lxml>=4.9.0',
    ],
    entry_points={
        'console_scripts': [
            'ibook=ibook_reader.cli:main',
        ],
    },
)
