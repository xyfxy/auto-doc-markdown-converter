"""
智能文档解析与 Markdown 转换器 (Auto Doc Markdown Converter)

这是一个功能强大的工具，旨在帮助用户轻松地将常见的文档格式（如 .docx 和 .pdf）
转换为结构清晰、易于阅读和编辑的 Markdown 文件。它利用先进的大型语言模型 (LLM) 技术，
智能地识别文档中的标题层级（H1-H4）和段落，确保转换后的 Markdown 文件能够准确反映原文的逻辑结构。
"""

__version__ = "1.0.0"
__author__ = "Auto Doc Markdown Converter Team"

# 导入核心功能
from .src.core_processor import process_document_to_markdown

__all__ = ['process_document_to_markdown'] 