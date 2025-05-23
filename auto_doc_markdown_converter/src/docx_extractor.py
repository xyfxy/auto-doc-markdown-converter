import docx
import logging

logger = logging.getLogger(__name__)

def extract_text_from_docx(file_path: str) -> str | None:
    """
    从 .docx 文件中提取所有文本，保留段落分隔。

    参数:
        file_path: .docx 文件的路径。

    返回:
        包含提取文本的字符串，段落之间用换行符分隔。
        如果发生错误，则返回 None。
    """
    try:
        logger.debug(f"开始从 DOCX 文件提取文本: {file_path}")
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        extracted_str = "\n".join(full_text)
        logger.debug(f"成功从 DOCX 文件提取文本: {file_path}")
        return extracted_str
    except docx.opc.exceptions.PackageNotFoundError:
        logger.error(f"无法打开或解析 DOCX 文件 (可能文件不存在、已损坏或不是有效的 DOCX 格式): {file_path}")
        return None
    except Exception as e:
        logger.error(f"从 DOCX 文件 {file_path} 提取文本时发生意外错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None