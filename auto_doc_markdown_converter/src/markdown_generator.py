import logging
import re # Import re module

# 获取模块特定的记录器
logger = logging.getLogger(__name__)

IMAGE_PLACEHOLDER_PATTERN = re.compile(r"\[IMAGE_PLACEHOLDER:([^\]]+)\]")

def generate_markdown_from_labeled_text(labeled_text: str) -> str:
    """
    将带标签的文本 (例如来自 LLM) 转换为 Markdown 格式。

    参数:
        labeled_text: 一个字符串，其中每行都应以类似 "H1:", "P:" 等标签为前缀。

    返回:
        包含转换后的 Markdown 文本的字符串。
    """
    if not labeled_text:
        logger.debug("输入 labeled_text 为空，返回空字符串。")
        return ""

    markdown_blocks = []
    lines = labeled_text.strip().split('\n')
    
    for i, line_raw in enumerate(lines): # 添加行号以便于调试
        line = line_raw.strip()
        if not line: # 跳过输入中的空行
            logger.debug(f"第 {i+1} 行为空，已跳过。")
            continue

        if line.startswith("H1: "):
            markdown_blocks.append(f"# {line[4:]}")
        elif line.startswith("H2: "):
            markdown_blocks.append(f"## {line[4:]}")
        elif line.startswith("H3: "):
            markdown_blocks.append(f"### {line[4:]}")
        elif line.startswith("H4: "):
            markdown_blocks.append(f"#### {line[4:]}")
        elif line.startswith("H5: "): # 新增
            markdown_blocks.append(f"##### {line[4:]}")
        elif line.startswith("H6: "): # 新增
            markdown_blocks.append(f"###### {line[4:]}")
        elif line.startswith("P: "):
            content = line[3:]
            # Process image placeholders in paragraph content
            content_parts = []
            last_end = 0
            for match in IMAGE_PLACEHOLDER_PATTERN.finditer(content):
                # Add text before the placeholder
                content_parts.append(content[last_end:match.start()])
                image_filename = match.group(1)
                # Assuming 'images' is the subdirectory where images are stored relative to the Markdown file
                markdown_image_link = f"![](images/{image_filename})"
                content_parts.append(markdown_image_link)
                last_end = match.end()
            # Add any remaining text after the last placeholder
            content_parts.append(content[last_end:])
            processed_content = "".join(content_parts)
            markdown_blocks.append(processed_content)
        else:
            logger.warning(f"第 {i+1} 行无法识别标签，已跳过: '{line_raw}'")
            # 继续到下一行，有效地跳过格式错误的行

    # 用两个换行符连接块，然后修剪开头/结尾多余的换行符。
    # 这确保了所有有效块之间的分隔。
    if not markdown_blocks:
        logger.debug("未生成 Markdown 块 (可能所有行都无法识别或输入在剥离后为空)。")
        return ""
        
    final_markdown = "\n\n".join(markdown_blocks).strip()
    logger.debug(f"成功生成 Markdown。预览 (前 100 个字符): {final_markdown[:100]}")
    return final_markdown
