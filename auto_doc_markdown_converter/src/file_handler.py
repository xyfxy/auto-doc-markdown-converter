import os
import logging
from .docx_extractor import extract_content_from_docx # Updated import
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


def read_file_content(filepath: str, file_type: str, results_dir: str | None = None) -> str | None:
    """
    Reads content from a supported file type using the appropriate extractor.
    Assumes file existence is checked by the caller.

    Args:
        filepath: The path to the file.
        file_type: The type of the file ("docx" or "pdf"), usually from get_file_type.
        results_dir: The directory where results (like images for docx) should be stored.
                     Required for "docx" type.

    Returns:
        The extracted text (as a string), or None if extraction fails or
        if the file type is not 'docx' or 'pdf'.
    """
    # Removed os.path.exists(filepath) check, as caller (e.g., core_processor) should handle it.

    try:
        if file_type == "docx":
            if not results_dir:
                logger.error(f"处理 DOCX 文件 {filepath} 时，results_dir 参数是必需的但未提供。")
                return None
            logger.info(f"正在从 DOCX 提取内容: {filepath} (结果将保存到 {results_dir})")
            return extract_content_from_docx(filepath, results_dir)
        elif file_type == "pdf":
            # pdf_extractor currently does not require results_dir for text extraction
            logger.info(f"正在从 PDF 提取文本: {filepath}")
            text = extract_text_from_pdf(filepath)
            if text is None or not text.strip():
                logger.warning(f"未能从 PDF {filepath} 提取文本。它可能是基于图像的、已加密的或空的。")
                return None
            return text
        else:
            logger.error(f"向 read_file_content 提供了不支持的文件类型 '{file_type}' 用于文件 '{filepath}'。")
            return None
    except Exception as e:
        logger.error(f"处理文件 {filepath} (类型: {file_type}) 时发生意外错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
