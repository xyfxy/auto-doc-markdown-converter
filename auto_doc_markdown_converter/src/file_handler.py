import os
import logging
from .docx_extractor import extract_text_from_docx
from .pdf_extractor import extract_text_from_pdf

SUPPORTED_EXTENSIONS = {".docx": "docx", ".pdf": "pdf"}

# Configure logging for this module if not configured by main application
# This ensures logs are captured even if file_handler is used standalone or tested separately.
logger = logging.getLogger(__name__)
if not logger.handlers: # Avoid adding multiple handlers if already configured
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_file_type(filepath: str) -> str:
    """
    Determines the type of the file based on its extension.

    Args:
        filepath: The path to the file.

    Returns:
        "docx", "pdf", or "unsupported".
    """
    if not filepath: # Handle empty filepath string
        logger.debug("get_file_type 收到一个空文件路径。") # 改为 DEBUG 级别
        return "unsupported"
    _, ext = os.path.splitext(filepath)
    return SUPPORTED_EXTENSIONS.get(ext.lower(), "unsupported")


def read_file_content(filepath: str, file_type: str) -> str | None:
    """
    Reads content from a supported file type using the appropriate extractor.
    假定文件存在性由调用方检查。

    Args:
        filepath: 文件的路径。
        file_type: 文件的类型 ("docx" 或 "pdf")，通常来自 get_file_type。

    Returns:
        提取的文本（字符串形式），如果提取失败、文件类型不是 'docx' 或 'pdf'，则为 None。
    """
    # 移除了 os.path.exists(filepath) 检查，因为调用方 (main.py) 应该已经检查过了。

    try:
        if file_type == "docx":
            logger.debug(f"正在从 DOCX 提取文本: {filepath}")
            return extract_text_from_docx(filepath)
        elif file_type == "pdf":
            logger.debug(f"正在从 PDF 提取文本: {filepath}")
            text = extract_text_from_pdf(filepath)
            if text is None or not text.strip(): # 检查文本是否为 None 或空/仅空白
                logger.warning(f"未能从 PDF 提取文本: {filepath}。它可能是基于图像的、已加密的或空的。")
                return None 
            return text
        else:
            # 如果调用方正确使用了 get_file_type，则理论上不应到达此路径。
            logger.error(f"向 read_file_content 提供了不支持的文件类型 '{file_type}' 用于文件: {filepath}。无法读取内容。") # 改为 ERROR
            return None
    except Exception as e: # 捕获提取器可能抛出的任何其他异常
        logger.error(f"处理文件 {filepath} (类型: {file_type}) 时发生意外错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
