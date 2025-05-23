# Placeholder for file handling logic 

import os
from .docx_extractor import extract_text_from_docx
from .pdf_extractor import extract_text_from_pdf

SUPPORTED_EXTENSIONS = {".docx", ".pdf"}

def validate_file(file_path: str) -> bool:
    """
    验证文件扩展名是否受支持。

    参数:
        file_path: 文件的路径。

    返回:
        如果支持则为 True，否则为 False。
    """
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in SUPPORTED_EXTENSIONS:
        print(f"错误: 文件类型 {ext} 不受支持。支持的类型为: {', '.join(SUPPORTED_EXTENSIONS)}")
        return False
    if not os.path.exists(file_path):
        print(f"错误: 文件未在 {file_path} 找到")
        return False
    return True

def read_file_content(file_path: str) -> str | None:
    """
    从受支持的文件类型中读取内容。

    参数:
        file_path: 文件的路径。

    返回:
        提取的文本（字符串形式），如果文件无效或提取失败则为 None。
    """
    if not validate_file(file_path):
        return None

    _, ext = os.path.splitext(file_path)
    extracted_text = ""

    try:
        if ext.lower() == ".docx":
            extracted_text = extract_text_from_docx(file_path)
        elif ext.lower() == ".pdf":
            extracted_text = extract_text_from_pdf(file_path)
            if not extracted_text: # pdf_extractor 在出错时可能返回空字符串
                print(f"警告: 无法从 PDF 中提取文本: {file_path}。它可能是基于图像的 PDF 或已加密。")
                return None # 如果 PDF 提取未产生任何内容，则显式返回 None
        return extracted_text
    except Exception as e:
        print(f"处理文件 {file_path} 时发生意外错误: {e}")
        return None

# 示例用法 (仅用于测试目的):
# if __name__ == '__main__':
#     # 在当前目录或特定的 test_files 目录中创建用于测试的虚拟文件
#     # 确保您有 sample.docx 和 sample.pdf (基于文本的) 才能使此示例工作。
#     # 为简单起见，此示例假定它们与 file_handler.py 在同一目录中，
#     # 或者您提供了完整路径。
#
#     # 虚拟 DOCX 创建 (需要 python-docx)
#     # import os # 如果 reportlab 部分处于活动状态，则已导入
#     from docx import Document
#     doc = Document()
#     doc.add_paragraph("来自 DOCX 的问候")
#     sample_docx = "sample_fh.docx"
#     doc.save(sample_docx)
#
#     # 虚拟 PDF 创建 (需要 reportlab)
#     try:
#         from reportlab.pdfgen import canvas
#         from reportlab.lib.pagesizes import letter
#         sample_pdf = "sample_fh.pdf"
#         c = canvas.Canvas(sample_pdf, pagesize=letter)
#         c.drawString(72, 750, "来自 PDF 的问候")
#         c.save()
#     except ImportError:
#         print("未安装 Reportlab，跳过 file_handler 测试的 PDF 虚拟文件创建。")
#         sample_pdf = None # 确保已定义
#
#     test_files = {
#         "docx_valid": sample_docx,
#         "pdf_valid": sample_pdf,
#         "unsupported": "sample.txt", # 为此创建一个虚拟 sample.txt
#         "non_existent": "non_existent_file.docx"
#     }
#
#     # 创建一个虚拟 txt 文件
#     with open("sample.txt", "w") as f:
#         f.write("这是一个文本文件。")
#
#     for file_type, file_name in test_files.items():
#         if file_name is None and file_type == "pdf_valid": # 如果 PDF 虚拟文件创建失败则跳过
#             print("\n由于无法创建虚拟文件，跳过 PDF 测试。")
#             continue
#         print(f"\n测试 {file_type}: {file_name}")
#         content = read_file_content(file_name)
#         if content:
#             print(f"提取的内容 (前 50 个字符): {content[:50]}...")
#         else:
#             print("未能提取内容或文件无效。")
#
#     # 清理虚拟文件
#     if os.path.exists(sample_docx):
#         os.remove(sample_docx)
#     if sample_pdf and os.path.exists(sample_pdf):
#         os.remove(sample_pdf)
#     if os.path.exists("sample.txt"):
#         os.remove("sample.txt") 