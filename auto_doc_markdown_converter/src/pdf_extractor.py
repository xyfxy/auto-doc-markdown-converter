import pdfplumber
import fitz  # PyMuPDF
import logging
import os
from typing import Tuple, Dict, Optional, List

logger = logging.getLogger(__name__)

# Dependency: PyMuPDF (fitz) is used for image extraction.
# Please ensure it is installed: pip install PyMuPDF

def _table_to_markdown(table_data: List[List[Optional[str]]]) -> str:
    """Converts a list of lists (table data) to a Markdown string."""
    markdown_lines = []
    if not table_data:
        return ""

    # Ensure all cells are strings, replacing None with empty string
    processed_table_data = []
    for row in table_data:
        processed_row = []
        for cell in row:
            cell_text = cell if cell is not None else ""
            # Escape Markdown special characters like | and newlines within cells
            cell_text = cell_text.replace('|', r'\|').replace('\n', ' <br> ')
            processed_row.append(cell_text.strip())
        processed_table_data.append(processed_row)

    if not processed_table_data:
        return ""

    # Create header row
    header_texts = processed_table_data[0]
    markdown_lines.append("| " + " | ".join(header_texts) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * len(header_texts)) + " |")

    # Process data rows
    for row in processed_table_data[1:]:
        markdown_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(markdown_lines)

def extract_content_from_pdf(file_path: str, results_dir: str) -> Optional[Tuple[str, Dict[str, str]]]:
    """
    从 .pdf 文件中提取文本、图片和表格。
    图片被保存，文本中的图片和表格被占位符替换。

    参数:
        file_path: .pdf 文件的路径。
        results_dir: 用于保存提取的图片等文件的目录。

    返回:
        一个元组 (text_with_placeholders, extracted_data)，其中:
        - text_with_placeholders: 包含所有占位符的文本字符串。
        - extracted_data: 一个字典，将占位符映射到其实际内容
                          (图片是文件名，表格是其 Markdown 字符串)。
        如果发生错误，则返回 None。
    """
    overall_content_parts: List[str] = []
    extracted_data: Dict[str, str] = {}
    image_counter = 0
    table_counter = 0

    images_sub_dir = os.path.join(results_dir, 'images')
    if not os.path.exists(images_sub_dir):
        try:
            os.makedirs(images_sub_dir, exist_ok=True)
            logger.info(f"创建图片子目录: {images_sub_dir}")
        except OSError as e:
            logger.error(f"创建图片子目录 {images_sub_dir} 失败: {e}")
            return None # Cannot proceed without image directory

    try:
        logger.debug(f"开始从 PDF 文件提取内容: {file_path}")

        # Using pdfplumber for text and table structure
        with pdfplumber.open(file_path) as pdf_plumber_doc:
            if not pdf_plumber_doc.pages:
                logger.warning(f"PDF 文件 {file_path} 不包含任何页面。")
                return "", {} # Return empty content if no pages

            # Using PyMuPDF for image extraction as it's more robust
            try:
                pymupdf_doc = fitz.open(file_path)
            except Exception as e:
                logger.error(f"使用 PyMuPDF 打开 PDF 文件 {file_path} 时出错: {e}. 图片提取功能将不可用。")
                pymupdf_doc = None


            for page_num, p_page in enumerate(pdf_plumber_doc.pages):
                page_content_parts: List[str] = []
                logger.debug(f"正在处理 PDF 文件 {file_path} 的第 {page_num + 1} 页...")

                # 1. 提取文本
                page_text = p_page.extract_text(x_tolerance=2, y_tolerance=2) # Adjust tolerance as needed
                if page_text:
                    page_content_parts.append(page_text.strip())

                # 2. 提取图片 (using PyMuPDF)
                if pymupdf_doc and page_num < len(pymupdf_doc):
                    pymu_page = pymupdf_doc.load_page(page_num)
                    image_list = pymu_page.get_images(full=True)
                    if image_list:
                        logger.debug(f"在第 {page_num + 1} 页找到 {len(image_list)} 张图片。")
                        for img_index, img_info in enumerate(image_list):
                            image_counter += 1
                            xref = img_info[0]
                            try:
                                base_image = pymupdf_doc.extract_image(xref)
                                image_bytes = base_image["image"]
                                image_ext = base_image["ext"]
                                
                                image_filename = f"pdf_image_{image_counter}.{image_ext}"
                                image_save_path = os.path.join(images_sub_dir, image_filename)
                                
                                with open(image_save_path, 'wb') as img_file:
                                    img_file.write(image_bytes)
                                logger.info(f"成功提取并保存图片: {image_save_path}")
                                
                                placeholder = f"[IMAGE_PLACEHOLDER:{image_filename}]"
                                page_content_parts.append(placeholder)
                                extracted_data[placeholder] = image_filename
                            except Exception as e:
                                logger.error(f"提取或保存图片 xref {xref} (计数器: {image_counter}) 时出错: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
                    else:
                        logger.debug(f"PDF 文件 {file_path} 的第 {page_num + 1} 页未检测到图片 (使用 PyMuPDF)。")
                elif pymupdf_doc is None:
                    logger.debug(f"PyMuPDF 文档对象不可用，跳过第 {page_num + 1} 页的图片提取。")


                # 3. 提取表格 (using pdfplumber)
                # extract_tables() is generally good for well-defined tables.
                # find_tables() + table.extract() gives more control if needed.
                try:
                    tables_on_page = p_page.extract_tables() # Returns list of tables, each table is list of lists
                    if tables_on_page:
                        logger.debug(f"在第 {page_num + 1} 页找到 {len(tables_on_page)} 个表格。")
                        for table_data in tables_on_page:
                            if not table_data: continue # Skip if table_data is empty or None

                            table_counter += 1
                            table_placeholder = f"[TABLE_PLACEHOLDER_{table_counter}]"
                            
                            markdown_table_str = _table_to_markdown(table_data)
                            if markdown_table_str:
                                extracted_data[table_placeholder] = markdown_table_str
                                page_content_parts.append(table_placeholder)
                                logger.debug(f"已提取并转换表格 {table_counter} 为 Markdown。")
                            else:
                                logger.warning(f"表格 {table_counter} (来自第 {page_num + 1} 页) 转换为空 Markdown，已跳过。")
                    else:
                        logger.debug(f"PDF 文件 {file_path} 的第 {page_num + 1} 页未检测到表格 (使用 pdfplumber)。")
                except Exception as e:
                    logger.error(f"在 PDF 文件 {file_path} 的第 {page_num + 1} 页提取表格时发生错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))

                if page_content_parts:
                    overall_content_parts.append("\n\n".join(page_content_parts))

            if pymupdf_doc:
                pymupdf_doc.close()

        if not overall_content_parts:
            logger.warning(f"未能从 PDF 文件 {file_path} 提取任何文本、图片或表格内容。")
            # If pdf_plumber_doc.pages was empty, we already returned.
            # This means pages existed but nothing could be extracted.
            return "", {} 
            
        final_text_with_placeholders = "\n\n".join(overall_content_parts)
        logger.info(f"成功从 PDF 文件提取内容: {image_counter} 张图片, {table_counter} 个表格。文件: {file_path}")
        return final_text_with_placeholders, extracted_data

    except pdfplumber.exceptions.PDFSyntaxError as pse:
        logger.error(f"解析 PDF 文件 {file_path} 时发生 pdfplumber 语法错误 (文件可能已损坏或格式不受支持): {pse}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
    except fitz.errors.FitzAuthError as fae: # PyMuPDF specific auth error
        logger.error(f"解析 PDF 文件 {file_path} 时发生 PyMuPDF 授权错误 (可能需要密码): {fae}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None
    except Exception as e:
        logger.error(f"从 PDF 文件 {file_path} 提取内容时发生意外错误: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return None