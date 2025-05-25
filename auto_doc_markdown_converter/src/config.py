"""
此模块负责从环境变量加载应用程序的核心配置。

这些配置主要用于与阿里云 DashScope 的 OpenAI 兼容模式 API 进行交互。
正确设置这些环境变量是程序成功运行的前提。

环境变量首先会尝试从项目根目录下的 .env 文件加载，如果 .env 文件不存在或未包含某些变量，
则会回退到从操作系统的环境变量中查找。

环境变量说明:
- LLM_API_KEY: 必需。您的阿里云 DashScope API 密钥。
               通常以 "sk-" 开头，例如 "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"。
- LLM_API_ENDPOINT: 必需。DashScope OpenAI 兼容模式的基础 URL。
                  例如："https://dashscope.aliyuncs.com/compatible-mode/v1"
- LLM_MODEL_ID: 可选。要使用的具体模型 ID。
                例如："qwen-plus", "qwen-turbo", "qwen-max"。
                如果未设置，应用程序将在 `llm_processor.py` 中使用默认模型 (当前为 "qwen-plus")。

如果关键配置（LLM_API_KEY 或 LLM_API_ENDPOINT）缺失，
程序在启动时会记录严重错误并引发 EnvironmentError 异常。
"""
import os
import logging
from dotenv import load_dotenv # 导入 load_dotenv

# 获取模块特定的记录器
logger = logging.getLogger(__name__)

# 尝试从 .env 文件加载环境变量
# .env 文件应该位于项目根目录 (即 config.py 往上两级目录)
# __file__ 是当前文件 (config.py) 的路径
# os.path.dirname(__file__) 是 src 目录
# os.path.dirname(os.path.dirname(__file__)) 是 auto_doc_markdown_converter 目录 (项目子根，如果src在里面)
# os.path.dirname(os.path.dirname(os.path.dirname(__file__))) 是真正的项目根目录
# 假设 src 目录位于项目根目录下的 auto_doc_markdown_converter 文件夹中
# 则 .env 文件应该在 auto_doc_markdown_converter 的父目录中
# 如果结构是 /project_root/auto_doc_markdown_converter/src/config.py
# 那么 .env 在 /project_root/.env
project_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
# 或者，如果 .env 和 main.py 同级，且 main.py 在项目根
# project_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')) # 如果config.py在src/下，.env在auto_doc_markdown_converter/下

# 最常见的情况是 .env 文件在项目的最顶层根目录
# 我们假设项目的结构是 /<project_root>/auto_doc_markdown_converter/src/config.py
# 则 .env 文件在 /<project_root>/.env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")) 
# 这个路径是根据当前文件 (auto_doc_markdown_converter/src/config.py) 计算的
# .. 返回到 auto_doc_markdown_converter/src
# .. 返回到 auto_doc_markdown_converter
# 所以，这里假设 .env 文件与 auto_doc_markdown_converter 文件夹同级，即在项目的根目录下。
# 如果项目结构是： auto-doc-markdown-converter (root) / .env
#                    auto-doc-markdown-converter (root) / auto_doc_markdown_converter (package) / src / config.py
# 则正确的路径应该是：
dotenv_path_correct = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

# 考虑到脚本可能从不同位置运行，我们尝试加载 .env (通常在项目根目录)
# load_dotenv() 会自动查找当前目录或父目录中的 .env 文件，通常这就够了
# 但为了明确性，可以指定路径。
# 假设 config.py 在 my_project/src/config.py，而 .env 在 my_project/.env
# 则 .env 路径是 os.path.join(os.path.dirname(__file__), "..", "..", ".env")
# 对于当前结构 /auto_doc_markdown_converter/auto_doc_markdown_converter/src/config.py
# .env 在 /auto_doc_markdown_converter/.env
final_dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".env")

if os.path.exists(final_dotenv_path):
    logger.info(f"正在从 {final_dotenv_path} 加载环境变量...")
    load_dotenv(dotenv_path=final_dotenv_path, override=True) # override=True 允许 .env 文件覆盖已存在的系统环境变量
else:
    logger.info(f".env 文件未在预期路径 {final_dotenv_path} 找到。将仅使用系统环境变量。")
    # 如果没有 .env 文件，load_dotenv() 不会报错，而是静默失败，后续 os.environ.get 会回退到系统变量
    load_dotenv(override=True) # 尝试从标准位置加载，如果存在的话

# 从环境变量中读取 API 密钥
# 此密钥用于授权对 DashScope API 的访问。
API_KEY = os.environ.get("LLM_API_KEY")

# 从环境变量中读取 API 端点
# 这是 DashScope OpenAI 兼容模式的基础 URL。
API_ENDPOINT = os.environ.get("LLM_API_ENDPOINT")

# 从环境变量中读取模型 ID (可选)
# 用户可以通过此变量指定要使用的 LLM 模型。
LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID")

# 检查必需的环境变量是否已设置
if API_KEY is None:
    logger.critical("关键配置缺失：环境变量 LLM_API_KEY 未找到 (请检查 .env 文件或系统环境变量)。这是访问 DashScope API 的必需凭证。")
    raise EnvironmentError("环境变量 LLM_API_KEY 未找到。请在运行应用程序之前设置它 (可配置于 .env 文件或系统环境变量)。")

if API_ENDPOINT is None:
    logger.critical("关键配置缺失：环境变量 LLM_API_ENDPOINT 未找到 (请检查 .env 文件或系统环境变量)。这是访问 DashScope API 的必需端点。")
    raise EnvironmentError("环境变量 LLM_API_ENDPOINT 未找到。请在运行应用程序之前设置它 (可配置于 .env 文件或系统环境变量)。")

# 记录模型 ID 的使用情况
if LLM_MODEL_ID:
    logger.info(f"LLM 模型 ID: {LLM_MODEL_ID} (来自 .env 文件或系统环境变量)")
else:
    logger.info("环境变量 LLM_MODEL_ID 未设置 (在 .env 文件或系统环境变量中均未找到)。应用程序将在 llm_processor.py 中使用默认模型 ID (例如 'qwen-plus')。")
