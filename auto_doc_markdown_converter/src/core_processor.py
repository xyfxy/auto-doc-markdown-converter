import os
import logging
from typing import Optional, List # 确保 List 也被导入
import concurrent.futures # 导入 concurrent.futures

from .file_handler import get_file_type, read_file_content
from .llm_processor import analyze_text_with_llm
from .markdown_generator import generate_markdown_from_labeled_text
from .config import API_KEY, API_ENDPOINT, LLM_MODEL_ID, MAX_CONCURRENT_LLM_REQUESTS # 导入 MAX_CONCURRENT_LLM_REQUESTS
from .text_splitter import ( # 导入文本分割相关函数和常量
    estimate_tokens,
    split_text_into_chunks,
    merge_processed_chunks,
    DEFAULT_MAX_CHUNK_TOKENS,
    DEFAULT_OVERLAP_TOKENS
)

# 用于决定何时启动长文本处理流程的阈值
# 直接使用 text_splitter 中的默认块大小作为参考
MAX_TOKENS_FOR_DIRECT_PROCESSING = DEFAULT_MAX_CHUNK_TOKENS
# logger 实例将在函数内部获取，或者如果已在模块级别定义则可直接使用
# 此处假设 logger 将在函数内通过 logging.getLogger(__name__) 获取

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
    # 在函数开始处记录长文本处理阈值
    logger.info(f"长文本处理阈值 (直接处理的最大 token 数): {MAX_TOKENS_FOR_DIRECT_PROCESSING}")
    logger.info(f"开始处理文档: {input_filepath}")

    # 1. 检查 API 配置 (关键步骤，确保核心功能可用)
    # LLM_MODEL_ID 不是必需的，llm_processor 有默认值，所以不在此处检查
    if not API_KEY:
        logger.critical("核心处理器错误：LLM_API_KEY 未配置。无法继续处理。")
        return None
    if not API_ENDPOINT:
        logger.critical("核心处理器错误：LLM_API_ENDPOINT 未配置。无法继续处理。")
        return None
    
    # 获取模型ID，供 estimate_tokens 和 split_text_into_chunks 使用 (如果它们内部需要)
    # llm_processor 内部会自行处理默认模型ID，这里主要是为 text_splitter 提供（如果其设计需要）
    # 当前 text_splitter.estimate_tokens 的 model_name 参数是 Optional 且未被使用。
    model_name_for_splitting = LLM_MODEL_ID # 可以是 None

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
        # Pass results_dir to read_file_content, especially for DOCX image extraction
        raw_text = read_file_content(input_filepath, file_type, results_dir)
        if raw_text is None:
            # read_file_content 内部已记录具体错误 (例如，文件为空或提取失败)
            logger.error(f"未能从文件 '{input_filepath}' 读取到有效内容。")
            return None
        logger.debug(f"成功从 '{input_filepath}' 读取内容 (前100字符预览: '{raw_text[:100].strip()}...')")
    except Exception as e:
        logger.error(f"读取文件 '{input_filepath}' 内容时发生意外的严重错误: {e}", exc_info=True)
        return None

    # 4. LLM 处理 (根据文本长度选择直接处理或分块处理)
    llm_output: Optional[str] = None # 初始化 llm_output
    try:
        num_estimated_tokens = estimate_tokens(raw_text, model_name=model_name_for_splitting)
        logger.info(f"提取的原始文本估算 token 数: {num_estimated_tokens} (模型用于估算: {model_name_for_splitting or '默认'})")
    except Exception as e_token:
        logger.error(f"估算原始文本 token 数时发生错误 ({input_filepath}): {e_token}", exc_info=True)
        return None # token 估算失败则无法继续

    if num_estimated_tokens <= MAX_TOKENS_FOR_DIRECT_PROCESSING:
        logger.info(f"文本 token 数 ({num_estimated_tokens}) 未超过阈值 ({MAX_TOKENS_FOR_DIRECT_PROCESSING})，直接进行 LLM 分析。")
        try:
            llm_output = analyze_text_with_llm(raw_text)
            if llm_output is None: # analyze_text_with_llm 内部已记录错误
                logger.error(f"直接 LLM 分析失败 ({input_filepath})。")
                return None 
        except Exception as e_llm_direct:
            logger.error(f"直接 LLM 分析文本内容时发生意外错误 ({input_filepath}): {e_llm_direct}", exc_info=True)
            return None
    else:
        logger.info(f"文本 token 数 ({num_estimated_tokens}) 超过阈值 ({MAX_TOKENS_FOR_DIRECT_PROCESSING})，启动长文本分块处理流程。")
        
        # 4.1. 分割文本
        try:
            original_text_chunks = split_text_into_chunks(
                raw_text,
                model_name=model_name_for_splitting, # 传递模型名称
                max_tokens_per_chunk=DEFAULT_MAX_CHUNK_TOKENS, # 使用导入的常量
                overlap_tokens=DEFAULT_OVERLAP_TOKENS      # 使用导入的常量
            )
            if not original_text_chunks:
                logger.error(f"文本分割后未产生任何有效文本块 ({input_filepath})。")
                return None
            logger.info(f"文本被分割成 {len(original_text_chunks)} 个原始块进行处理。")
        except Exception as e_split:
            logger.error(f"文本分割过程中发生错误 ({input_filepath}): {e_split}", exc_info=True)
            return None

        # 4.2. 分块处理
        processed_chunks_results: List[Optional[str]] = [None] * len(original_text_chunks) # 初始化结果列表以保持顺序
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_LLM_REQUESTS) as executor:
            future_to_chunk_index = {
                executor.submit(analyze_text_with_llm, chunk): i
                for i, chunk in enumerate(original_text_chunks)
            }

            for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk_index)):
                original_index = future_to_chunk_index[future]
                try:
                    chunk_result = future.result()
                    if chunk_result is None:
                        logger.error(f"处理文本块 {original_index + 1} (原始顺序) 失败 ({input_filepath})。中止长文本处理。")
                        # 取消其他所有未完成的 future
                        for f in future_to_chunk_index:
                            if not f.done():
                                f.cancel()
                        return None
                    processed_chunks_results[original_index] = chunk_result
                    logger.info(f"文本块 {original_index + 1}/{len(original_text_chunks)} (原始顺序) 处理完成。")
                except concurrent.futures.CancelledError:
                    logger.warning(f"文本块 {original_index + 1} (原始顺序) 的处理被取消。")
                    # 如果一个任务被取消（通常是因为另一个任务失败），则整体失败
                    return None
                except Exception as e_llm_chunk:
                    logger.error(f"处理文本块 {original_index + 1} (原始顺序) 时发生意外错误 ({input_filepath}): {e_llm_chunk}", exc_info=True)
                    # 取消其他所有未完成的 future
                    for f in future_to_chunk_index:
                        if not f.done():
                            f.cancel()
                    return None
        
        # 检查是否有任何块处理失败 (理论上如果上面逻辑正确，这里不会是 None，除非 analyze_text_with_llm 返回 None 但未抛异常)
        if any(result is None for result in processed_chunks_results):
            logger.error(f"一个或多个文本块未能成功处理 ({input_filepath})。")
            return None

        # 将 List[Optional[str]] 转换为 List[str] 给 merge_processed_chunks
        # 此时可以安全地假设没有 None 值，因为上面已经检查过了
        final_processed_chunks = [str(chunk) for chunk in processed_chunks_results]


        # 4.3. 合并结果
        if not final_processed_chunks: 
             logger.error(f"所有文本块处理后均未产生有效结果 ({input_filepath})。")
             return None

        logger.info(f"所有 {len(final_processed_chunks)} 个块均已处理，开始合并结果...")
        try:
            # 确保 merge_processed_chunks 接收的是 List[str]
            llm_output = merge_processed_chunks(
                final_processed_chunks, # 使用转换后的列表
                original_text_chunks,
                overlap_tokens=DEFAULT_OVERLAP_TOKENS,
                model_name=model_name_for_splitting
            )
            if not llm_output: # merge_processed_chunks 返回空字符串或None
                logger.error(f"合并所有已处理文本块后结果为空 ({input_filepath})。")
                return None
            logger.info("所有文本块结果合并完成。")
        except Exception as e_merge:
            logger.error(f"合并已处理文本块时发生错误 ({input_filepath}): {e_merge}", exc_info=True)
            return None
    
    # 确保 llm_output 在进入 Markdown 生成前有值（如果前面逻辑正确，应该有，除非直接处理或分块处理都失败了）
    if llm_output is None:
        logger.error(f"LLM 处理步骤未能生成任何输出内容 ({input_filepath})。")
        return None
    logger.debug(f"LLM 处理完成，最终输出 (前100字符预览: '{llm_output[:100].strip()}...')")

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
