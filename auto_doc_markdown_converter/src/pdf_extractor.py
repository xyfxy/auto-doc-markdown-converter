import pdfplumber
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str | None:
    """
    从基于文本的 .pdf 文件中提取所有文本，并尽可能保留段落分隔。

    参数:
        file_path: .pdf 文件的路径。

    返回:
        包含提取文本的字符串。如果发生错误，则返回 None。
    """
    full_text = []
    try:
        logger.debug(f"开始从 PDF 文件提取文本: {file_path}")
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                logger.warning(f"PDF 文件 {file_path} 不包含任何页面。")
                return None # 或者返回空字符串，取决于期望的行为
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    full_text.append(page_text)
                else:
                    logger.debug(f"PDF 文件 {file_path} 的第 {i+1} 页未提取到文本。")
        
        if not full_text:
            logger.warning(f"未能从 PDF 文件 {file_path} 提取任何文本内容 (可能是基于图像的 PDF)。")
            return None # 或 ""
            
        extracted_str = "\n".join(full_text)
        logger.debug(f"成功从 PDF 文件提取文本: {file_path}")
        return extracted_str
    except pdfplumber.exceptions.PDFSyntaxError as pse:
        logger.error(f"解析 PDF 文件 {file_path} 时发生语法错误 (文件可能已损坏或格式不受支持): {pse}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
    except Exception as e:
        logger.error(f"从 PDF 文件 {file_path} 提取文本时发生意外错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None