import logging
from typing import Optional, List
import re # 用于后续的 split_text_into_chunks

logger = logging.getLogger(__name__)

# 调整后的字符与 token 的近似转换比率
DEFAULT_CHAR_TO_TOKEN_RATIO = 2.0 

def estimate_tokens(text: str, model_name: Optional[str] = None) -> int: # model_name 暂时保留，但不再使用
    """
    估算给定文本的 token 数量。
    当前实现仅基于字符数和预设的 DEFAULT_CHAR_TO_TOKEN_RATIO进行估算。
    参数:
        text (str): 需要估算 token 数的文本。
        model_name (Optional[str]): (当前未使用) 未来可能用于选择特定模型的估算方法。
    返回:
        int: 估算的 token 数量。
    """
    if not text:
        return 0
    num_tokens = int(len(text) / DEFAULT_CHAR_TO_TOKEN_RATIO) 
    return num_tokens

# --- 文本分割逻辑 ---
DEFAULT_MAX_CHUNK_TOKENS = 7000  # 每个块的最大目标 token 数
DEFAULT_OVERLAP_TOKENS = 300     # 块之间的目标重叠 token 数

def _split_text_by_sentences(paragraph_text: str) -> List[str]:
    if not paragraph_text:
        return []
    sentence_parts = re.split(r'([。？！.!?\n]+)', paragraph_text)
    sentences = []
    current_sentence_parts: List[str] = []
    for part in sentence_parts:
        if not part: 
            continue
        current_sentence_parts.append(part)
        if re.search(r'[。？！.!?\n]$', part):
            sentence_candidate = "".join(current_sentence_parts)
            if sentence_candidate.strip(): 
                sentences.append(sentence_candidate)
            current_sentence_parts = []
    if current_sentence_parts: 
        remaining_text = "".join(current_sentence_parts)
        if remaining_text.strip():
            sentences.append(remaining_text)
    if not sentences and paragraph_text.strip(): 
        logger.debug(f"段落未能按标准标点分割成句子，视为单个句子处理：'{paragraph_text[:100].replace(chr(10), chr(92)+'n')}'")
        return [paragraph_text]
    return sentences

def _hard_split_segment(segment_text: str, max_tokens: int, overlap_tokens_target: int, model_name: str) -> List[str]:
    sub_chunks: List[str] = []
    if not segment_text.strip():
        return sub_chunks
    target_chars_for_max_tokens = int(max_tokens * DEFAULT_CHAR_TO_TOKEN_RATIO)
    target_chars_for_overlap = int(overlap_tokens_target * DEFAULT_CHAR_TO_TOKEN_RATIO)
    if target_chars_for_max_tokens <= 0: target_chars_for_max_tokens = 1 
    if target_chars_for_overlap < 0: target_chars_for_overlap = 0
    if target_chars_for_overlap >= target_chars_for_max_tokens and target_chars_for_max_tokens > 0 : 
        target_chars_for_overlap = int(target_chars_for_max_tokens * 0.2) 
        logger.warning(f"硬分割中目标重叠 ({overlap_tokens_target} tokens) 过大或等于块大小，已调整为目标块字符数的20% ({target_chars_for_overlap} chars)。")
    elif target_chars_for_max_tokens == 0 : 
        target_chars_for_overlap = 0
    current_pos = 0
    text_len = len(segment_text)
    while current_pos < text_len:
        start_char_of_current_sub_chunk = current_pos 
        end_pos = min(current_pos + target_chars_for_max_tokens, text_len)
        sub_chunk = segment_text[current_pos:end_pos]
        if not sub_chunk.strip() and end_pos < text_len: 
            current_pos = end_pos 
            continue
        sub_chunks.append(sub_chunk)
        if end_pos >= text_len: break
        current_pos = end_pos - target_chars_for_overlap
        if current_pos <= start_char_of_current_sub_chunk : 
             old_current_pos = current_pos
             current_pos = end_pos 
             logger.debug(f"硬分割中重叠计算导致无法前进或重叠等于整个块 (原计划 next_start={old_current_pos}, 当前块起始={start_char_of_current_sub_chunk})。切换为从当前子块末尾 ({end_pos}) 开始 (无重叠)。")
        if current_pos >= text_len: break
    return [sc for sc in sub_chunks if sc.strip()]

def split_text_into_chunks(
    text: str,
    model_name: str = 'qwen-long', 
    max_tokens_per_chunk: int = DEFAULT_MAX_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS
) -> List[str]:
    if not text.strip():
        logger.debug("输入文本为空或仅包含空白，返回空列表。")
        return []
    logger.info(f"开始文本分割。目标块 token 数: {max_tokens_per_chunk}, 目标重叠 token 数: {overlap_tokens}。")
    raw_segments_with_separators = re.split(r'(\n{2,})', text) 
    initial_segments: List[str] = []
    buffer = ""
    for item in raw_segments_with_separators:
        if not item: continue 
        if re.fullmatch(r'\n{2,}', item): 
            if buffer: 
                initial_segments.append(buffer + item) 
                buffer = ""
            elif initial_segments and not initial_segments[-1].endswith("\n\n"): 
                 initial_segments[-1] = initial_segments[-1].rstrip('\n') + "\n\n"
        else: 
            buffer += item
    if buffer: 
        initial_segments.append(buffer)
    processed_segments: List[str] = []
    for segment in initial_segments:
        stripped_segment_for_token_estimation = segment.strip() 
        if not stripped_segment_for_token_estimation:
            if segment and processed_segments and processed_segments[-1].strip():
                 if not processed_segments[-1].endswith("\n\n"): 
                      processed_segments[-1] = processed_segments[-1].rstrip("\n") + "\n\n"
            continue 
        segment_token_count = estimate_tokens(stripped_segment_for_token_estimation, model_name)
        if segment_token_count > max_tokens_per_chunk:
            sentences = _split_text_by_sentences(segment) 
            if sentences:
                processed_segments.extend(sentences)
            else: 
                processed_segments.append(segment) 
        else:
            processed_segments.append(segment) 
    final_segments = [seg for seg in processed_segments if seg.strip()] 
    logger.debug(f"按段落和句子细分并去除纯空白片段后，总计 {len(final_segments)} 个文本片段。")
    chunks: List[str] = []
    current_chunk_buffer: List[str] = []
    current_chunk_estimated_tokens: int = 0
    for seg_idx, segment_text in enumerate(final_segments):
        segment_tokens = estimate_tokens(segment_text, model_name)
        if segment_tokens > max_tokens_per_chunk:
            logger.debug(f"片段 #{seg_idx+1} (估算 {segment_tokens} tokens) 自身已超长，将进行硬分割。")
            if current_chunk_buffer: 
                chunks.append("".join(current_chunk_buffer))
                current_chunk_buffer = []
                current_chunk_estimated_tokens = 0
            hard_split_sub_chunks = _hard_split_segment(segment_text, max_tokens_per_chunk, overlap_tokens, model_name)
            chunks.extend(hard_split_sub_chunks)
            current_chunk_buffer = [] 
            current_chunk_estimated_tokens = 0
            if chunks and overlap_tokens > 0 and hard_split_sub_chunks: 
                 last_hard_chunk = chunks[-1] 
                 overlap_chars_count = int(overlap_tokens * DEFAULT_CHAR_TO_TOKEN_RATIO * 0.8) 
                 if len(last_hard_chunk) > overlap_chars_count:
                     overlap_text = last_hard_chunk[-overlap_chars_count:]
                     if overlap_text.strip(): 
                         current_chunk_buffer = [overlap_text]
                         current_chunk_estimated_tokens = estimate_tokens(overlap_text, model_name)
            continue 
        if not current_chunk_buffer or (current_chunk_estimated_tokens + segment_tokens <= max_tokens_per_chunk):
            current_chunk_buffer.append(segment_text)
            current_chunk_estimated_tokens += segment_tokens
        else:
            chunk_to_add = "".join(current_chunk_buffer)
            chunks.append(chunk_to_add)
            if overlap_tokens > 0:
                temp_overlap_str = ""
                accumulated_overlap_tokens_val = 0 
                for i in range(len(current_chunk_buffer) - 1, -1, -1):
                    prev_segment = current_chunk_buffer[i]
                    prev_segment_tokens = estimate_tokens(prev_segment, model_name)
                    if (accumulated_overlap_tokens_val + prev_segment_tokens <= overlap_tokens * 1.1) or not temp_overlap_str: 
                        temp_overlap_str = prev_segment + temp_overlap_str
                        accumulated_overlap_tokens_val += prev_segment_tokens
                    else:
                        break 
                current_chunk_buffer = [temp_overlap_str] if temp_overlap_str.strip() else []
                current_chunk_estimated_tokens = estimate_tokens(temp_overlap_str, model_name) if temp_overlap_str.strip() else 0
            else: 
                current_chunk_buffer = []
                current_chunk_estimated_tokens = 0
            if current_chunk_estimated_tokens + segment_tokens > max_tokens_per_chunk and \
               current_chunk_estimated_tokens > 0 and \
               current_chunk_buffer and \
               current_chunk_buffer[0].strip() and \
               segment_text.strip() : 
                 chunks.append("".join(current_chunk_buffer)) 
                 current_chunk_buffer = [segment_text] 
                 current_chunk_estimated_tokens = segment_tokens
            else: 
                 if not current_chunk_buffer or not current_chunk_buffer[0].strip(): 
                      current_chunk_buffer = [segment_text]
                      current_chunk_estimated_tokens = segment_tokens
                 else: 
                      current_chunk_buffer.append(segment_text)
                      current_chunk_estimated_tokens += segment_tokens
    if current_chunk_buffer and "".join(current_chunk_buffer).strip():
        chunks.append("".join(current_chunk_buffer))
    final_chunks = [chunk for chunk in chunks if chunk.strip()]
    logger.info(f"文本成功被分割成 {len(final_chunks)} 个非空文本块。")
    return final_chunks

# --- 结果合并逻辑 ---

def merge_processed_chunks(
    processed_chunks: List[str],
    original_text_chunks: Optional[List[str]] = None, 
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS, 
    model_name: Optional[str] = None 
) -> str:
    """
    合并由 LLM 处理后的文本块列表，尝试移除重叠部分。
    此实现基于行比较来检测和移除重叠。

    参数:
        processed_chunks: LLM 处理后的文本块列表 (带标记字符串)。
        original_text_chunks: (当前未使用，但为未来更精确合并保留) 分割前的原始文本块。
        overlap_tokens: 分割时设置的目标重叠 token 数，用于辅助判断。
        model_name: (当前未使用) 模型名称。

    返回:
        str: 合并后的单一 Markdown 字符串。
    """
    if not processed_chunks:
        logger.info("没有已处理的块可供合并，返回空字符串。")
        return ""

    if len(processed_chunks) == 1:
        logger.info("只有一个块，无需合并，直接返回该块内容。")
        return processed_chunks[0].strip()

    # 第一个块直接全部接受
    merged_lines: List[str] = processed_chunks[0].splitlines()
    # logger.debug(f"合并：初始内容来自第一个块，包含 {len(merged_lines)} 行。")

    # 定义启发式检查的行数
    avg_chars_per_line = 40  # 假设平均每行字符数 (经验值)
    avg_tokens_per_line = estimate_tokens("a" * avg_chars_per_line, model_name) 
    if avg_tokens_per_line == 0: avg_tokens_per_line = 1 # 避免除以零
    
    # 动态计算检查的行数上限，但设定一个合理的硬上限以避免性能问题
    max_overlap_lines_heuristic = 15 
    if overlap_tokens > 0 and avg_tokens_per_line > 0:
        # 允许一些余量，例如多检查几行
        calculated_lines = int(overlap_tokens / avg_tokens_per_line * 1.2) + 3 
        max_overlap_lines_heuristic = min(calculated_lines, 20) # 硬上限为20行

    if overlap_tokens > 0 : 
        logger.debug(f"合并时将检查最多 {max_overlap_lines_heuristic} 行的重叠（基于 overlap_tokens: {overlap_tokens}）。")


    for i in range(1, len(processed_chunks)):
        current_chunk_text = processed_chunks[i]
        if not current_chunk_text.strip():
            logger.debug(f"合并：跳过第 {i+1} 个已处理块，因为它为空或仅含空白。")
            continue

        current_chunk_lines = current_chunk_text.splitlines()
        if not current_chunk_lines: 
            logger.debug(f"合并：跳过第 {i+1} 个已处理块，因为它在按行分割后为空。")
            continue
            
        if not merged_lines: 
            logger.debug(f"合并：之前的合并结果为空，直接使用第 {i+1} 个块。")
            merged_lines = current_chunk_lines
            continue
        
        num_lines_to_check = min(len(merged_lines), len(current_chunk_lines), max_overlap_lines_heuristic) if max_overlap_lines_heuristic > 0 else 0
        
        actual_overlap_rows = 0
        if num_lines_to_check > 0:
            for k in range(num_lines_to_check, 0, -1): 
                prev_suffix_stripped = [line.strip() for line in merged_lines[-k:]]
                current_prefix_stripped = [line.strip() for line in current_chunk_lines[:k]]

                if prev_suffix_stripped == current_prefix_stripped:
                    is_meaningful_overlap = False
                    for line_content in prev_suffix_stripped: 
                        if len(line_content) > 3: # 假设超过3个非空白字符的行是有意义的重叠
                            is_meaningful_overlap = True
                            break
                    if is_meaningful_overlap or k <= 1: # 单行重叠即使短也认为是重叠
                        actual_overlap_rows = k
                        break 
        
        if actual_overlap_rows > 0:
            logger.debug(f"合并：在与第 {i+1} 个块比较时，发现 {actual_overlap_rows} 行重叠。")
            non_overlapping_current_lines = current_chunk_lines[actual_overlap_rows:]
            
            if non_overlapping_current_lines:
                # 追加非重叠行
                merged_lines.extend(non_overlapping_current_lines)
                # logger.debug(f"  已追加 {len(non_overlapping_current_lines)} 条非重叠行。")
            # else: 当前块完全被前一个块的重叠部分覆盖，不添加任何内容
        else: # 未发现有意义的行重叠
            logger.debug(f"合并：未发现明显行重叠，直接拼接第 {i+1} 个块的行。")
            # 如果 merged_lines 的最后一行不是空行 (即没有以段落分隔符结束)
            # 并且 current_chunk_lines 的第一行也不是空行 (即不是以段落分隔符开始)
            # 则在它们之间添加一个空行以表示段落分隔。
            if merged_lines and merged_lines[-1].strip() != "" and current_chunk_lines[0].strip() != "":
                # 检查是否已经有足够的换行符
                if not merged_lines[-1].endswith("\n\n") and not merged_lines[-1].endswith("\n \n"): # 检查是否已经是段落结尾
                     if not (len(merged_lines) >1 and merged_lines[-1].strip()=="" and merged_lines[-2].strip()!=""): # 不是刚刚加过空行
                        merged_lines.append("") # 添加一个空行作为分隔
            
            merged_lines.extend(current_chunk_lines)
    
    final_text = "\n".join(merged_lines)
    # 移除首尾多余的空白，并确保最终文本以单个换行符结尾（如果非空）
    final_text = final_text.strip()
    if final_text:
        final_text += "\n" # 确保末尾有一个换行

    logger.info(f"所有块合并完成。最终输出长度 {len(final_text)}。")
    return final_text
