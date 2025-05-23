import os
import logging
from typing import Optional # 用于类型提示

from .file_handler import get_file_type, read_file_content
from .llm_processor import analyze_text_with_llm
from .markdown_generator import generate_markdown_from_labeled_text
from .config import API_KEY, API_ENDPOINT

def process_document_to_markdown(input_filepath: str, results_dir: str) -> Optional[str]:
    """
    处理单个文档（.docx 或 .pdf），将其转换为 Markdown 文件并保存到指定目录。

    该函数封装了文档处理的核心逻辑：文件类型识别、内容读取、LLM 分析、
    Markdown 生成以及结果保存。

    参数:
        input_filepath (str): 要处理的单个文档的完整路径。
        results_dir (str): 用于保存生成的 .md 文件的目录路径。

    返回:
        Optional[str]: 如果处理成功，则返回生成的 Markdown 文件的完整路径。
                       如果任何步骤失败或文件不受支持，则返回 None。
    """
    logger = logging.getLogger(__name__)
    logger.info(f"开始处理文档: {input_filepath}")

    # 1. 检查 API 配置 (关键步骤，确保核心功能可用)
    if not API_KEY:
        logger.critical("核心处理器错误：LLM_API_KEY 未配置。无法继续处理。")
        return None
    if not API_ENDPOINT:
        logger.critical("核心处理器错误：LLM_API_ENDPOINT 未配置。无法继续处理。")
        return None

    # 2. 获取文件类型
    logger.debug(f"正在获取文件 '{input_filepath}' 的类型...")
    file_type = get_file_type(input_filepath)
    if file_type == "unsupported":
        logger.warning(f"文件 '{os.path.basename(input_filepath)}' 类型不受支持。已跳过。")
        return None
    logger.debug(f"文件类型识别为: {file_type}")

    # 3. 读取文件内容
    logger.debug(f"正在从 '{input_filepath}' (类型: {file_type}) 读取内容...")
    try:
        raw_text = read_file_content(input_filepath, file_type)
        if raw_text is None:
            # read_file_content 内部已记录具体错误 (例如，文件为空或提取失败)
            logger.error(f"未能从文件 '{input_filepath}' 读取到有效内容。")
            return None
        logger.debug(f"成功从 '{input_filepath}' 读取内容 (前100字符预览: '{raw_text[:100].strip()}...')")
    except Exception as e:
        logger.error(f"读取文件 '{input_filepath}' 内容时发生意外的严重错误: {e}", exc_info=True)
        return None

    # 4. LLM 处理
    logger.debug(f"正在使用 LLM 分析从 '{input_filepath}' 提取的文本...")
    try:
        llm_output = analyze_text_with_llm(raw_text)
        if llm_output is None:
            # analyze_text_with_llm 内部已记录具体错误 (例如，API 调用失败或响应无效)
            logger.error(f"LLM 分析来自 '{input_filepath}' 的文本失败。")
            return None
        logger.debug(f"LLM 分析完成 (前100字符预览: '{llm_output[:100].strip()}...')")
    except Exception as e:
        logger.error(f"使用 LLM 分析来自 '{input_filepath}' 的文本时发生意外的严重错误: {e}", exc_info=True)
        return None

    # 5. Markdown 生成
    logger.debug(f"正在从 LLM 输出为 '{input_filepath}' 生成 Markdown...")
    try:
        markdown_content = generate_markdown_from_labeled_text(llm_output)
        if markdown_content is None or not markdown_content.strip(): # 检查是否为 None 或空/仅空白
            logger.error(f"从 LLM 输出为 '{input_filepath}' 生成 Markdown 时出错，结果为空或无效。")
            return None
        logger.debug(f"Markdown 生成成功 (前100字符预览: '{markdown_content[:100].strip()}...')")
    except Exception as e:
        logger.error(f"从 LLM 输出为 '{input_filepath}' 生成 Markdown 时发生意外的严重错误: {e}", exc_info=True)
        return None

    # 6. 保存 Markdown 文件
    try:
        # 确保 results_dir 目录存在
        os.makedirs(results_dir, exist_ok=True)
        logger.debug(f"确保结果目录 '{results_dir}' 已存在。")

        # 构造输出文件名和路径
        base_name = os.path.splitext(os.path.basename(input_filepath))[0] + ".md"
        output_md_path = os.path.join(results_dir, base_name)
        logger.debug(f"Markdown 输出路径构造为: {output_md_path}")

        # 写入文件
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        logger.info(f"成功将处理后的 Markdown 内容保存到: {output_md_path}")
        return output_md_path  # 返回生成的 Markdown 文件路径

    except IOError as e:
        logger.error(f"写入 Markdown 文件 '{output_md_path}' 时发生IO错误: {e}", exc_info=True)
        return None
    except OSError as e: # os.makedirs 可能抛出 OSError
        logger.error(f"创建结果目录 '{results_dir}' 时发生错误: {e}", exc_info=True)
        return None
    except Exception as e: # 捕获其他可能的意外错误
        logger.error(f"保存 Markdown 文件到 '{output_md_path}' 时发生意外的严重错误: {e}", exc_info=True)
        return None
