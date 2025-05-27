import os
import logging
from typing import Optional, Tuple, Dict # Added Tuple, Dict

from .docx_extractor import extract_content_from_docx
from .pdf_extractor import extract_content_from_pdf # Updated to new function name potentially

SUPPORTED_EXTENSIONS = {".docx": "docx", ".pdf": "pdf"}

# Configure logging for this module if not configured by main application
# This ensures logs are captured even if file_handler is used standalone or tested separately.
logger = logging.getLogger(__name__)
# Removed basicConfig to avoid conflict with main app's logging setup
# if not logger.handlers: # Avoid adding multiple handlers if already configured
#     logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


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


def read_file_content(filepath: str, file_type: str, results_dir: str) -> Optional[Tuple[str, Dict[str, str]]]:
    """
    Reads content (text, image placeholders, table placeholders) from a supported file type.
    Assumes file existence is checked by the caller.

    Args:
        filepath: The path to the file.
        file_type: The type of the file ("docx" or "pdf").
        results_dir: The directory where results (like images) should be stored.
                     This is now required for both docx and pdf.

    Returns:
        A tuple (text_with_placeholders, extracted_data_dict) or None if extraction fails.
        - text_with_placeholders: String containing text and placeholders.
        - extracted_data_dict: Dictionary mapping placeholders to their content
                               (e.g., image filename or Markdown table).
    """
    if not results_dir: # results_dir is now crucial for both types if they produce images/data
        logger.error(f"处理文件 {filepath} (类型: {file_type}) 时，results_dir 参数是必需的但未提供。")
        return None

    try:
        if file_type == "docx":
            logger.info(f"正在从 DOCX 提取内容: {filepath} (结果将保存到 {results_dir})")
            # extract_content_from_docx already returns Optional[Tuple[str, Dict[str, str]]]
            return extract_content_from_docx(filepath, results_dir)
        elif file_type == "pdf":
            logger.info(f"正在从 PDF 提取内容: {filepath} (结果将保存到 {results_dir})")
            # extract_content_from_pdf should also return Optional[Tuple[str, Dict[str, str]]]
            content_tuple = extract_content_from_pdf(filepath, results_dir)
            if content_tuple is None:
                logger.warning(f"未能从 PDF {filepath} 提取内容。返回 None。")
                return None
            text_content, extracted_data = content_tuple
            if text_content is None or (not text_content.strip() and not extracted_data): # Check if both text and data are empty
                logger.warning(f"从 PDF {filepath} 提取的内容为空 (无文本且无提取数据)。")
                # Return empty text and data instead of None if extraction itself didn't fail
                return "", {} 
            return text_content, extracted_data
        else:
            logger.error(f"向 read_file_content 提供了不支持的文件类型 '{file_type}' 用于文件 '{filepath}'。")
            return None
    except Exception as e:
        logger.error(f"处理文件 {filepath} (类型: {file_type}) 时发生意外错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
