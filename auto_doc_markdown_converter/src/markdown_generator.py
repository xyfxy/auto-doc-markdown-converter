import logging
import re
from typing import Optional, Dict

# 获取模块特定的记录器
logger = logging.getLogger(__name__)

# Regex to find image placeholders like [IMAGE_PLACEHOLDER:filename.jpg]
IMAGE_PLACEHOLDER_RE = re.compile(r"\[IMAGE_PLACEHOLDER:([^\]]+)\]")
# Regex to find table placeholders like [TABLE_PLACEHOLDER_1]
TABLE_PLACEHOLDER_RE = re.compile(r"\[TABLE_PLACEHOLDER_(\d+)\]")


def generate_markdown_from_labeled_text(
    labeled_text: str, 
    extracted_data: Optional[Dict[str, str]] = None
) -> str:
    """
    将带标签的文本 (例如来自 LLM) 转换为 Markdown 格式。
    同时，使用 extracted_data 中的信息替换文本中的图片和表格占位符。

    参数:
        labeled_text: 一个字符串，其中每行都应以类似 "H1:", "P:" 等标签为前缀。
        extracted_data: 一个可选字典，将占位符映射到其内容 (图片是文件名，表格是 Markdown 字符串)。

    返回:
        包含转换后的 Markdown 文本的字符串。
    """
    if not labeled_text:
        logger.debug("输入 labeled_text 为空，返回空字符串。")
        return ""

    markdown_blocks = []
    lines = labeled_text.strip().split('\n')
    
    for i, line_raw in enumerate(lines):
        line = line_raw.strip()
        if not line:
            logger.debug(f"第 {i+1} 行为空，已跳过。")
            continue

        # Current logic for converting labeled lines to basic Markdown structure
        if line.startswith("H1: "):
            markdown_blocks.append(f"# {line[4:]}")
        elif line.startswith("H2: "):
            markdown_blocks.append(f"## {line[4:]}")
        elif line.startswith("H3: "):
            markdown_blocks.append(f"### {line[4:]}")
        elif line.startswith("H4: "):
            markdown_blocks.append(f"#### {line[4:]}")
        elif line.startswith("H5: "):
            markdown_blocks.append(f"##### {line[4:]}")
        elif line.startswith("H6: "):
            markdown_blocks.append(f"###### {line[4:]}")
        elif line.startswith("P: "):
            # Content after "P: " is kept as is, placeholders will be replaced later
            markdown_blocks.append(line[3:])
        # elif line.startswith("[IMAGE_PLACEHOLDER:") or line.startswith("[TABLE_PLACEHOLDER_"):
            # If a placeholder is on its own line after LLM processing (e.g. LLM returned it as P: [PLACEHOLDER])
            # it will be handled by the paragraph logic above or direct replacement pass later.
            # For now, we assume placeholders might also be part of other text lines.
            # No special handling here, will be caught by the global replacement pass.
        #    markdown_blocks.append(line) # Keep the placeholder line as is for now
        else:
            # If line doesn't match known labels, and is not a placeholder on its own line,
            # it might be a continuation of a previous block or just unlabelled text.
            # For simplicity, and to avoid losing content, append it directly.
            # This might need refinement based on LLM output patterns.
            # If it's a placeholder from extracted_data, it will be replaced later.
            logger.debug(f"第 {i+1} 行无法识别主要标签，将作为普通文本块处理: '{line_raw}'")
            markdown_blocks.append(line)


    if not markdown_blocks:
        logger.debug("未生成初步 Markdown 块。")
        return ""
        
    # First pass: Join basic markdown blocks
    intermediate_markdown = "\n\n".join(markdown_blocks).strip()

    # Second pass: Replace placeholders using extracted_data
    if extracted_data:
        final_markdown = intermediate_markdown
        for placeholder_key, content_value in extracted_data.items():
            escaped_placeholder_key = re.escape(placeholder_key)
            if placeholder_key.startswith("[IMAGE_PLACEHOLDER:"):
                # Extract filename from placeholder_key e.g., "[IMAGE_PLACEHOLDER:image_1.png]" -> "image_1.png"
                match = IMAGE_PLACEHOLDER_RE.fullmatch(placeholder_key)
                if match:
                    image_filename = match.group(1)
                    # Assume images are in 'images/' subdirectory relative to the Markdown file
                    markdown_image_link = f"![](images/{image_filename})"
                    final_markdown = re.sub(escaped_placeholder_key, markdown_image_link, final_markdown)
                    logger.debug(f"图片占位符 '{placeholder_key}' 已替换为 '{markdown_image_link}'。")
                else:
                    logger.warning(f"无法从图片占位符 '{placeholder_key}' 解析图片文件名。")
            elif placeholder_key.startswith("[TABLE_PLACEHOLDER_"):
                # content_value is already the Markdown table string
                final_markdown = re.sub(escaped_placeholder_key, content_value, final_markdown)
                logger.debug(f"表格占位符 '{placeholder_key}' 已替换。")
            else:
                logger.warning(f"extracted_data 中的未知占位符类型: '{placeholder_key}'。")
        
        # Fallback for any image or table placeholders that might not have been in extracted_data
        # or were part of the original text and not caught by extracted_data keys.
        # This handles placeholders if they were directly in the LLM output text.
        
        # Fallback for image placeholders not in extracted_data (should be rare)
        def replace_image_match(match):
            image_filename = match.group(1)
            logger.warning(f"在文本中找到图片占位符 '{match.group(0)}' 但它不在 extracted_data 中，将尝试直接转换。")
            return f"![](images/{image_filename})"
        final_markdown = IMAGE_PLACEHOLDER_RE.sub(replace_image_match, final_markdown)

        # Fallback for table placeholders not in extracted_data (even rarer, tables should always be in extracted_data)
        def replace_table_match(match):
            placeholder = match.group(0)
            logger.warning(f"在文本中找到表格占位符 '{placeholder}' 但它不在 extracted_data 中，占位符将被保留。")
            return placeholder # Keep placeholder if no data for it
        final_markdown = TABLE_PLACEHOLDER_RE.sub(replace_table_match, final_markdown)

    else:
        # If no extracted_data, still perform a pass for any placeholders that might be in the text from LLM
        final_markdown = intermediate_markdown
        def replace_image_match_no_data(match):
            image_filename = match.group(1)
            logger.warning(f"找到图片占位符 '{match.group(0)}' 但无 extracted_data 提供，将尝试直接转换。")
            return f"![](images/{image_filename})"
        final_markdown = IMAGE_PLACEHOLDER_RE.sub(replace_image_match_no_data, final_markdown)

        def replace_table_match_no_data(match):
            placeholder = match.group(0)
            logger.warning(f"找到表格占位符 '{placeholder}' 但无 extracted_data 提供，占位符将被保留。")
            return placeholder
        final_markdown = TABLE_PLACEHOLDER_RE.sub(replace_table_match_no_data, final_markdown)


    logger.debug(f"成功生成 Markdown。预览 (前 100 个字符): {final_markdown[:100]}")
    return final_markdown.strip()
