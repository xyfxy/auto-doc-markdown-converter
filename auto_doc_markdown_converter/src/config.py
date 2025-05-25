"""
此模块负责从环境变量加载应用程序的核心配置。

这些配置主要用于与阿里云 DashScope 的 OpenAI 兼容模式 API 进行交互。
正确设置这些环境变量是程序成功运行的前提。

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

# 获取模块特定的记录器
logger = logging.getLogger(__name__)

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
    logger.critical("关键配置缺失：环境变量 LLM_API_KEY 未找到。这是访问 DashScope API 的必需凭证。")
    raise EnvironmentError("环境变量 LLM_API_KEY 未找到。请在运行应用程序之前设置它。")

if API_ENDPOINT is None:
    logger.critical("关键配置缺失：环境变量 LLM_API_ENDPOINT 未找到。这是访问 DashScope API 的必需端点。")
    raise EnvironmentError("环境变量 LLM_API_ENDPOINT 未找到。请在运行应用程序之前设置它。")

# 记录模型 ID 的使用情况
if LLM_MODEL_ID:
    logger.info(f"检测到环境变量 LLM_MODEL_ID，将优先使用模型 ID: {LLM_MODEL_ID}")
else:
    logger.info("环境变量 LLM_MODEL_ID 未设置。应用程序将在 llm_processor.py 中使用默认模型 ID (例如 'qwen-plus')。")

# LLM API 调用超时时间 (单位：秒)
# 从环境变量 LLM_API_CALL_TIMEOUT 读取，如果未设置，则默认为 300 秒 (5分钟)
# 使用 os.getenv 是为了方便处理环境变量未设置时返回 None 的情况，然后我们可以提供默认值。
# int() 转换确保了我们得到的是整数类型。
LLM_API_CALL_TIMEOUT_STR = os.environ.get("LLM_API_CALL_TIMEOUT", "300")
try:
    LLM_API_CALL_TIMEOUT = int(LLM_API_CALL_TIMEOUT_STR)
    if LLM_API_CALL_TIMEOUT <= 0:
        logger.warning(f"环境变量 LLM_API_CALL_TIMEOUT 的值 '{LLM_API_CALL_TIMEOUT_STR}' 不是一个正整数，将使用默认值 300 秒。")
        LLM_API_CALL_TIMEOUT = 300
except ValueError:
    logger.warning(f"环境变量 LLM_API_CALL_TIMEOUT 的值 '{LLM_API_CALL_TIMEOUT_STR}' 不是有效的整数，将使用默认值 300 秒。")
    LLM_API_CALL_TIMEOUT = 300
logger.info(f"LLM API 调用超时时间配置为: {LLM_API_CALL_TIMEOUT} 秒")
