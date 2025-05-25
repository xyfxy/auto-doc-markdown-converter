"""
auto_doc_markdown_converter.src 包初始化文件。

此包包含了应用程序的核心处理逻辑、模块化组件以及配置。
通过导入 `process_document_to_markdown` 函数，提供了一个便捷的
核心功能调用入口。同时，也使得 `config` 和 `utils` 等基础模块
可以从包级别访问。
"""
# 导入项目的主要配置和工具
from . import config
from . import utils

# 导入各个处理模块 (这些通常由核心处理器或主应用间接使用)
from . import docx_extractor
from . import pdf_extractor
from . import file_handler
from . import llm_processor
from . import markdown_generator

# 导入并导出核心处理函数，使其可从 src 包直接访问
from .core_processor import process_document_to_markdown

# 导入并导出文本分割相关函数
from .text_splitter import estimate_tokens, split_text_into_chunks

# 也导入 text_splitter 模块本身，如果需要的话
from . import text_splitter # 确保 text_splitter 模块被导入


# 定义 __all__ 以明确指定从 "from src import *" 时应导入的内容
# 这有助于控制命名空间并提供清晰的公共 API。
__all__ = [
    'config',           # 应用程序配置
    'utils',            # 通用工具函数 (例如 setup_logging)
    'process_document_to_markdown', # 核心文档处理函数
    'estimate_tokens',  # Token 估算函数
    'split_text_into_chunks', # 文本分割函数
    'text_splitter',    # 文本分割模块 (如果希望用户能通过 src.text_splitter 访问)
    # 以下模块通常不直接从 src 导入，而是通过其功能被调用，但可以根据需要添加
    # 'file_handler',
    # 'llm_processor',
    # 'markdown_generator',
    # 'docx_extractor',
    # 'pdf_extractor',
    # 'core_processor', # 模块本身通常不导出，而是导出其函数
]
