"""
主命令行界面 (CLI) 模块。

该模块负责解析命令行参数，初始化应用程序，并协调各个子模块
(如文件处理、LLM分析、Markdown生成) 来完成文档转换任务。
"""
import argparse
import os # 保留 os 是为了 os.listdir，尽管 pathlib.Path.iterdir() 是一个选项
import logging
from pathlib import Path

# Project-specific imports
# 移除了不再直接使用的导入：get_file_type, read_file_content, analyze_text_with_llm, generate_markdown_from_labeled_text
from src.config import API_KEY, API_ENDPOINT # 仍然需要用于初始检查
from src.utils import setup_logging # 导入新的日志设置函数
from src.core_processor import process_document_to_markdown # 导入新的核心处理函数

# Basic Logging Configuration - 将被移除
# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main_cli():
    """
    命令行界面主函数。
    解析参数，设置日志，并按顺序调用处理模块。
    """
    parser = argparse.ArgumentParser(description="自动将各种格式的文档转换为 Markdown，并使用 LLM 进行处理。")
    parser.add_argument("input_path", type=str, help="输入文件（.docx, .pdf）或目录的路径。")
    parser.add_argument("output_dir", type=str, help="保存 Markdown 文件的目录路径。")
    parser.add_argument("-v", "--verbose", action="store_true", help="启用详细输出以进行调试。")

    args = parser.parse_args()

    # 初始化日志记录
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level) # 调用新的日志设置函数

    # 获取一个名为 'main' 的记录器实例，或者使用根记录器
    logger = logging.getLogger(__name__) # 或者 logging.getLogger("auto_doc_markdown_converter.main")

    # 1. 初始检查
    logger.debug("正在执行初始检查...")
    if not API_KEY:
        logger.critical("LLM_API_KEY 未设置。请设置此环境变量。程序即将退出。") # 使用更严重的级别
        return 1 
    if not API_ENDPOINT: 
        logger.critical("LLM_API_ENDPOINT 未设置。请设置此环境变量。程序即将退出。") # 使用更严重的级别
        return 1
    
    logger.info(f"使用的 LLM API 密钥: {'*' * (len(API_KEY) - 4) + API_KEY[-4:] if API_KEY else '未设置'}")
    logger.info(f"使用的 LLM API 端点: {API_ENDPOINT if API_ENDPOINT else '未设置'}")

    input_path = Path(args.input_path)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        logger.error(f"输入路径不存在: {input_path}")
        return 1

    try:
        output_dir.mkdir(parents=True, exist_ok=True) 
        logger.info(f"确保输出目录已创建: {output_dir}")
    except OSError as e:
        logger.error(f"无法创建输出目录 {output_dir}: {e}")
        return 1

    # 2. 文件处理逻辑
    logger.debug("开始文件处理逻辑...")
    files_to_process = []
    if input_path.is_file():
        if input_path.suffix.lower() in ['.docx', '.pdf']:
            files_to_process.append(input_path)
        else:
            logger.warning(f"输入文件 {input_path.name} 不是 .docx 或 .pdf 文件。已跳过。")
    elif input_path.is_dir():
        logger.info(f"正在处理目录中的文件: {input_path}")
        try:
            # 使用 pathlib.Path.iterdir() 替代 os.listdir()
            for item_path in input_path.iterdir():
                if item_path.is_file() and item_path.suffix.lower() in ['.docx', '.pdf']:
                    files_to_process.append(item_path)
        except OSError as e:
            logger.error(f"无法读取目录 {input_path} 中的文件: {e}")
            return 1 # 如果无法列出目录，则退出
    else:
        logger.error(f"输入路径 {input_path} 不是有效的文件或目录。")
        return 1
        
    if not files_to_process:
        logger.info("在指定的输入路径中未找到要处理的 .docx 或 .pdf 文件。")
        return 0

    processed_count = 0
    error_count = 0

    for file_path_obj in files_to_process: 
        full_input_file_path_str = str(file_path_obj)
        # file_name_for_logging = file_path_obj.name # core_processor 内部会记录文件名

        # 调用核心处理函数
        # logger.info(f"正在处理文件: {file_name_for_logging}...") # core_processor 会记录开始处理
        
        # 注意：我们将 output_dir (Path 对象) 转换为字符串，因为 core_processor 当前期望字符串路径
        result_md_path = process_document_to_markdown(str(file_path_obj), str(output_dir))

        if result_md_path:
            logger.info(f"文件 '{file_path_obj.name}' 已成功处理并保存到 '{result_md_path}'。")
            processed_count += 1
        else:
            # process_document_to_markdown 内部已记录详细错误日志
            logger.error(f"处理文件 '{file_path_obj.name}' 失败。详情请查看之前的日志。")
            error_count += 1

    logger.info(f"处理完成。成功处理 {processed_count} 个文件，发生 {error_count} 个错误。")
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    # 注意：如果 setup_logging 在 main_cli 内部，则直接运行此脚本时，
    # 在解析参数之前的任何日志记录（例如，在导入时）都将使用默认配置。
    # 这通常是可以接受的，因为主要的应用日志记录是在 main_cli 调用 setup_logging 之后开始的。
    exit_code = main_cli()
    exit(exit_code)
