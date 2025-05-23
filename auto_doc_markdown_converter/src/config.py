"""
此模块负责从环境变量加载应用程序配置。

主要配置包括：
- LLM_API_KEY: 大语言模型服务的 API 密钥。
- LLM_API_ENDPOINT: 大语言模型服务的 API 端点。阿里云百炼的端点通常格式为 `https://bailian.aliyuncs.com/v2/models/apps/text_generation/do`，但用户应从其控制台获取准确值。
- LLM_MODEL_ID: (可选) 特定的模型 ID。如果未设置，应用程序可能会使用默认模型。

如果关键配置（如 API_KEY 或 API_ENDPOINT）缺失，程序启动时会记录严重错误并可能引发异常或无法正常运行。
"""
import os
import logging

# 获取模块特定的记录器
logger = logging.getLogger(__name__)

API_KEY = os.environ.get("LLM_API_KEY")
API_ENDPOINT = os.environ.get("LLM_API_ENDPOINT") # 例如: "https://bailian.aliyuncs.com/v2/models/apps/text_generation/do"
LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID") # 例如: "qwen-plus", "qwen-turbo"

if API_KEY is None:
    logger.critical("关键配置缺失：环境变量 LLM_API_KEY 未找到。应用程序无法在没有 API 密钥的情况下运行。")
    raise EnvironmentError("环境变量 LLM_API_KEY 未找到。请在运行应用程序之前设置它。")

if API_ENDPOINT is None:
    logger.critical("关键配置缺失：环境变量 LLM_API_ENDPOINT 未找到。应用程序需要 API 端点才能运行。")
    # 考虑到 main.py 也会检查并因此退出，这里也抛出错误以保持一致性。
    raise EnvironmentError("环境变量 LLM_API_ENDPOINT 未找到。请在运行应用程序之前设置它。")

if LLM_MODEL_ID:
    logger.info(f"检测到环境变量 LLM_MODEL_ID，将使用模型 ID: {LLM_MODEL_ID}")
else:
    logger.info("环境变量 LLM_MODEL_ID 未设置。应用程序将在 llm_processor.py 中使用默认模型 ID。")
