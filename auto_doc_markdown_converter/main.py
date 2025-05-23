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
from src.file_handler import get_file_type, read_file_content
from src.llm_processor import analyze_text_with_llm
from src.markdown_generator import generate_markdown_from_labeled_text
from src.config import API_KEY, API_ENDPOINT # To check if they are set
from src.utils import setup_logging # 导入新的日志设置函数

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
        file_name_for_logging = file_path_obj.name 

        logger.info(f"正在处理文件: {file_name_for_logging}...")
        try:
            file_type = get_file_type(full_input_file_path_str)
            if file_type == "unsupported":
                logger.warning(f"文件 {file_name_for_logging} 类型不受支持。已跳过。")
                error_count += 1
                continue

            logger.debug(f"正在从 {file_name_for_logging} (类型: {file_type}) 读取内容...")
            raw_text = read_file_content(full_input_file_path_str, file_type)
            if raw_text is None: # read_file_content 在发生错误时返回 None
                logger.error(f"未能从 {file_name_for_logging} 读取内容。已在 read_file_content 中记录具体错误。已跳过。")
                error_count += 1
                continue
            if not raw_text.strip(): # 检查是否为空或仅有空白字符
                logger.warning(f"从 {file_name_for_logging} 提取的内容为空或仅包含空白字符。已跳过 LLM 处理。")
                error_count += 1
                continue
            
            logger.debug(f"提取的文本 (前 200 个字符): '{raw_text[:200].strip()}...'")

            logger.debug(f"正在使用 LLM 分析来自 {file_name_for_logging} 的文本...")
            llm_output = analyze_text_with_llm(raw_text)
            if llm_output is None : # 假设 analyze_text_with_llm 在严重错误时返回 None
                 logger.error(f"LLM 分析 {file_name_for_logging} 失败。已在 analyze_text_with_llm 中记录具体错误。已跳过。")
                 error_count +=1
                 continue
            logger.debug(f"LLM 输出 (前 200 个字符): '{llm_output[:200].strip()}...'")

            logger.debug(f"正在为 {file_name_for_logging} 生成 Markdown...")
            markdown_content = generate_markdown_from_labeled_text(llm_output)
            logger.debug(f"Markdown 内容 (前 200 个字符): '{markdown_content[:200].strip()}...'")

            base_name_for_output = file_path_obj.stem + ".md"
            output_file_path = output_dir / base_name_for_output
            
            logger.debug(f"准备将 Markdown 保存到: {output_file_path}")
            try:
                # 检查文件是否存在，并记录日志
                if output_file_path.exists():
                    logger.info(f"输出文件 {output_file_path} 已存在，将被覆盖。")
                else:
                    logger.debug(f"将创建新的输出文件：{output_file_path}")

                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                logger.info(f"已成功将 Markdown 内容保存到：{output_file_path.name} (在目录 {output_dir} 中)")

            except PermissionError: # 更具体的异常捕获
                logger.error(f"无法写入输出文件 {output_file_path}：权限不足。请检查输出目录的写入权限。")
                error_count += 1
                continue # 跳到下一个文件
            except IOError as e: # 其他 IO 错误
                logger.error(f"写入输出文件 {output_file_path} 时发生IO错误：{e}")
                error_count += 1
                continue # 跳到下一个文件
            except Exception as e: # 捕获其他在文件写入过程中可能发生的意外错误
                logger.error(f"保存输出文件 {output_file_path} 时发生预料之外的错误：{e}", exc_info=args.verbose)
                error_count += 1
                continue # 跳到下一个文件
            
            logger.info(f"已成功处理并将 {file_name_for_logging} 转换为 {base_name_for_output}") # 调整了成功日志的位置和内容
            processed_count += 1
        
        except ValueError as ve: # 例如，LLM 密钥/端点问题可能在 analyze_text_with_llm 中引发 ValueError
            logger.error(f"处理 {file_name_for_logging} 时发生配置或值错误: {ve}", exc_info=args.verbose)
            error_count += 1
        except Exception as e: # 捕获其他意外错误
            logger.error(f"处理 {file_name_for_logging} 时发生意外错误: {e}", exc_info=args.verbose)
            error_count += 1

    logger.info(f"处理完成。成功处理 {processed_count} 个文件，发生 {error_count} 个错误。")
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    # 注意：如果 setup_logging 在 main_cli 内部，则直接运行此脚本时，
    # 在解析参数之前的任何日志记录（例如，在导入时）都将使用默认配置。
    # 这通常是可以接受的，因为主要的应用日志记录是在 main_cli 调用 setup_logging 之后开始的。
    exit_code = main_cli()
    exit(exit_code)
