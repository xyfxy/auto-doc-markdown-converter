import logging
import requests
# 从 .config 模块导入所有需要的配置项
from .config import API_KEY, API_ENDPOINT, LLM_MODEL_ID, LLM_API_CALL_TIMEOUT 

# 获取模块特定的记录器
logger = logging.getLogger(__name__)

# 默认的 DashScope OpenAI 兼容模式模型 ID (如果环境变量 LLM_MODEL_ID 未设置)
DEFAULT_DASHSCOPE_MODEL_ID = "qwen-plus" 
# 旧的 DEFAULT_API_TIMEOUT 常量将被移除或注释掉
# # 默认的 API 超时时间
# DEFAULT_API_TIMEOUT = 60 # 秒

def analyze_text_with_llm(text: str) -> str | None:
    """
    使用阿里云 DashScope OpenAI 兼容模式分析给定文本以识别标题和段落。

    参数:
        text: 要分析的文本。

    返回:
        LLM 识别的包含标题和段落的结构化文本。
        如果发生严重错误或 API 调用失败，则返回 None。
    """
    # --- Mock LLM 调用已移除，恢复真实 API 调用逻辑 ---
    # logger.info("LLM 分析被 Mock，返回固定模拟输出。")
    # return "H1: 模拟标题\nP: 这是一个通过 Mock LLM 生成的模拟段落。"

    if not API_KEY:
        logger.critical("DashScope API 密钥 (LLM_API_KEY) 未配置。")
        return None

    if not API_ENDPOINT:
        logger.critical("DashScope API 端点 (LLM_API_ENDPOINT) 未配置。")
        return None
        
    # 使用 config 模块中定义的 LLM_MODEL_ID，如果为 None，则使用此处的默认值
    llm_model_id = LLM_MODEL_ID if LLM_MODEL_ID else DEFAULT_DASHSCOPE_MODEL_ID
    logger.info(f"使用的 DashScope (OpenAI 兼容模式) 模型 ID: {llm_model_id}")

    system_prompt = (
        "你是一个专业的文档结构分析助手。"
        "请分析用户提供的文本内容，并将其中的各级标题（H1, H2, H3, H4）和段落（P）准确地识别出来。"
        "请严格按照以下格式输出每一项内容，每项占一行：'标签: 内容'。"
        "例如：'H1: 这是一个一级标题' 或 'P: 这是一个段落。'。"
        "在你的回答中，不要包含任何解释性文字、开场白或总结。"
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # OpenAI 兼容模式的请求体
    payload = {
        "model": llm_model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        # 根据需要，可以在这里添加其他 OpenAI 兼容的参数，例如 temperature, max_tokens (如果服务器支持在请求体中覆盖)
        # "max_tokens": 2000, # 示例：如果需要显式设置
    }
    
    # 构建目标 URL
    target_url = f"{API_ENDPOINT.rstrip('/')}/chat/completions"

    logger.info(f"正在向 DashScope OpenAI 兼容模式 API 端点 {target_url} 发送请求 (模型: {llm_model_id})。")
    logger.debug(f"发送的请求体 (部分，不含文本): {{'model': '{llm_model_id}', 'messages': [{{'role': 'system', 'content': '...'}}, {{'role': 'user', 'content': '...'[:50] + '...'}}]}}")

    try:
        # 使用从 config 模块导入的 LLM_API_CALL_TIMEOUT
        response = requests.post(target_url, headers=headers, json=payload, timeout=LLM_API_CALL_TIMEOUT)
        response.raise_for_status()  # 对 HTTP 错误状态码 (4XX 或 5XX) 引发 HTTPError

        response_json = response.json()
        logger.info("已成功从 DashScope OpenAI 兼容模式 API 收到响应。")
        logger.debug(f"收到的原始 JSON 响应: {response_json}")

        # 从 OpenAI 兼容的响应中提取文本
        if (response_json.get("choices") and
            isinstance(response_json["choices"], list) and
            len(response_json["choices"]) > 0 and
            response_json["choices"][0].get("message") and
            isinstance(response_json["choices"][0]["message"], dict) and # 确保 message 是一个字典
            response_json["choices"][0]["message"].get("content")):
            
            processed_text = response_json["choices"][0]["message"]["content"]
            if processed_text:
                logger.debug(f"从 DashScope API 提取的文本内容 (前100字符): {processed_text[:100]}")
                return processed_text.strip() # 移除可能的首尾空白
            else:
                logger.warning("DashScope API 响应的 'choices[0].message.content' 字段为空。")
                return None
        else:
            logger.error(f"DashScope API 响应格式不符合预期，未找到 'choices[0].message.content'。响应详情: {response_json}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"请求 DashScope API 端点 {target_url} 超时 (超时设置为 {LLM_API_CALL_TIMEOUT} 秒)。")
        return None
    except requests.exceptions.HTTPError as e:
        error_details = f"HTTP 状态码: {e.response.status_code}"
        try:
            error_response_json = e.response.json()
            # 尝试解析 OpenAI 兼容的错误结构
            if "error" in error_response_json and isinstance(error_response_json["error"], dict) and "message" in error_response_json["error"]:
                error_details += f", 错误信息: {error_response_json['error']['message']}"
                if "type" in error_response_json["error"]:
                     error_details += f", 类型: {error_response_json['error']['type']}"
                if "code" in error_response_json["error"]: # DashScope 可能也用 code
                     error_details += f", Code: {error_response_json['error']['code']}"
            elif "code" in error_response_json and "message" in error_response_json: # 备用：检查类似百炼的错误结构
                error_details += f", Code: {error_response_json['code']}, Message: {error_response_json['message']}"
            else: # 如果没有标准错误结构，则使用原始文本
                error_details += f", 原始响应: {e.response.text}"
        except ValueError: # 如果响应体不是 JSON
            error_details += f", 原始响应: {e.response.text}"
        
        # DashScope 在 HTTP 错误时，响应头中可能有 x-request-id
        request_id = e.response.headers.get("x-request-id")
        if request_id:
            error_details += f", RequestId: {request_id}"
            
        logger.error(f"DashScope API 请求失败。{error_details}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
    except requests.exceptions.RequestException as e: # 其他 requests 库相关的网络层异常
        logger.error(f"调用 DashScope API 时发生网络请求错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
    except Exception as e: # 捕获其他意外错误，例如 response.json() 解析失败
        logger.error(f"处理 DashScope API 响应时发生未预料的错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
