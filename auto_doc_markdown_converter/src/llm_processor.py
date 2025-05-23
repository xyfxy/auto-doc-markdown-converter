import logging
import requests
import os # 用于读取 LLM_MODEL_ID 环境变量
from . import config

# 获取模块特定的记录器
logger = logging.getLogger(__name__)

# 默认的百炼模型 ID (如果环境变量未设置)
DEFAULT_BAILIAN_MODEL_ID = "qwen-plus" 
# 默认的百炼 API 超时时间
DEFAULT_API_TIMEOUT = 60 # 秒

def analyze_text_with_llm(text: str) -> str | None:
    """
    使用阿里云百炼 LLM 分析给定文本以识别标题和段落。

    参数:
        text: 要分析的文本。

    返回:
        LLM 识别的包含标题和段落的结构化文本。
        如果发生严重错误或 API 调用失败，则返回 None。
    """
    if not config.API_KEY:
        logger.critical("百炼 LLM API 密钥 (LLM_API_KEY) 未配置。")
        return None

    if not config.API_ENDPOINT:
        logger.critical("百炼 LLM API 端点 (LLM_API_ENDPOINT) 未配置。")
        return None
        
    # 从环境变量读取模型 ID，如果未设置则使用默认值
    # 注意：config.LLM_MODEL_ID 应该在 config.py 中定义，这里我们直接读取 os.environ 仅作演示
    # 正确的做法是在 config.py 中添加 LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID", DEFAULT_BAILIAN_MODEL_ID)
    # 然后在这里使用 config.LLM_MODEL_ID
    llm_model_id = os.environ.get("LLM_MODEL_ID", DEFAULT_BAILIAN_MODEL_ID)
    logger.info(f"使用的百炼模型 ID: {llm_model_id}")


    system_prompt = (
        "你是一个专业的文档结构分析助手。"
        "请分析用户提供的文本内容，并将其中的各级标题（H1, H2, H3, H4）和段落（P）准确地识别出来。"
        "请严格按照以下格式输出每一项内容，每项占一行：'标签: 内容'。"
        "例如：'H1: 这是一个一级标题' 或 'P: 这是一个段落。'。"
        "在你的回答中，不要包含任何解释性文字、开场白或总结。"
    )

    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json",
        # 根据百炼文档，如果需要流式输出，则添加 'X-DashScope-SSE: enable'
        # 当前为非流式，可选择添加 'X-DashScope-SSE: disable' 或不加（取决于 API 默认行为）
    }

    payload = {
        "model": llm_model_id,
        "input": {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        },
        "parameters": {
            # "max_tokens": 2000, # 根据百炼 API 文档，max_tokens 可能用于控制输出长度
            # 如果 API 支持，可以设置 temperature, top_p 等参数
            # "result_format": "text", # 如果 API 支持指定响应格式
        }
    }
    # 清理 parameters，如果其中没有实际参数则移除该键，避免API报错
    if not payload["parameters"]:
        del payload["parameters"]


    logger.info(f"正在向百炼 LLM 端点 {config.API_ENDPOINT} 发送请求 (模型: {llm_model_id})。")
    logger.debug(f"发送的请求体 (部分，不含文本): {{'model': '{llm_model_id}', 'input': {{'messages': [{{'role': 'system', 'content': '...'}}, {{'role': 'user', 'content': '...'[:50] + '...'}}]}}}}")

    try:
        response = requests.post(config.API_ENDPOINT, headers=headers, json=payload, timeout=DEFAULT_API_TIMEOUT)
        response.raise_for_status()  # 对 HTTP 错误状态码 (4XX 或 5XX) 引发 HTTPError

        response_json = response.json()
        logger.info("已成功从百炼 LLM 收到响应。")
        logger.debug(f"收到的原始 JSON 响应: {response_json}") # 记录完整响应以便调试

        # 根据百炼 API 文档，提取生成的文本
        # 假设文本在 response_json["output"]["text"]
        if "output" in response_json and "text" in response_json["output"]:
            processed_text = response_json["output"]["text"]
            if processed_text:
                logger.debug(f"从百炼 LLM 提取的文本内容 (前100字符): {processed_text[:100]}")
                return processed_text.strip() # 移除可能的首尾空白
            else:
                logger.warning("百炼 LLM 响应的 output.text 字段为空。")
                return None
        else:
            # 检查是否有错误信息
            if "code" in response_json and "message" in response_json:
                 error_code = response_json["code"]
                 error_message = response_json["message"]
                 logger.error(f"百炼 LLM API 返回业务错误。代码: {error_code}, 消息: {error_message}, RequestId: {response_json.get('request_id')}")
            else:
                logger.error(f"百炼 LLM 响应格式不符合预期，未找到 'output.text'。响应详情: {response_json}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"请求百炼 LLM 端点 {config.API_ENDPOINT} 超时 (超时设置为 {DEFAULT_API_TIMEOUT} 秒)。")
        return None
    except requests.exceptions.HTTPError as e:
        # 尝试解析响应体中的错误信息
        error_details = ""
        try:
            error_response_json = e.response.json()
            if "code" in error_response_json and "message" in error_response_json:
                error_details = f"错误码: {error_response_json['code']}, 错误信息: {error_response_json['message']}, RequestId: {error_response_json.get('request_id')}"
            else:
                error_details = e.response.text
        except ValueError: # 如果响应体不是 JSON
            error_details = e.response.text
        logger.error(f"百炼 LLM API 请求失败，HTTP 状态码 {e.response.status_code}。详情: {error_details}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
    except requests.exceptions.RequestException as e: # 其他 requests 库相关的网络层异常
        logger.error(f"调用百炼 LLM API 时发生网络请求错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
    except Exception as e: # 捕获其他意外错误，例如 response.json() 解析失败
        logger.error(f"处理百炼 LLM 响应时发生未预料的错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
