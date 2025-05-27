import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template # 确保导入 render_template
from werkzeug.utils import secure_filename

# 临时解决方案：将项目根目录添加到 sys.path 以便导入 src 模块
# 假设 webapp 目录位于项目根目录下
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auto_doc_markdown_converter.src.core_processor import process_document_to_markdown
# 如果 src/__init__.py 中导出了 process_document_to_markdown，也可以用：
# from auto_doc_markdown_converter.src import process_document_to_markdown
from auto_doc_markdown_converter.src.utils import setup_logging # 导入日志设置

# 初始化 Flask 应用
app = Flask(__name__)

# 配置上传文件和结果文件的存储目录
# UPLOAD_FOLDER 和 RESULTS_FOLDER 的定义与之前相同
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
RESULTS_FOLDER = os.path.join(BASE_DIR, 'results')

# 确保这些目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 限制上传大小为 32MB

# 获取 Flask 应用的 logger 实例
# 在 debug=True 模式下，Flask 会自动配置一个基本的 StreamHandler
# 如果需要更复杂的日志（例如写入文件），可以在非 debug 模式下配置
logger = app.logger # 直接使用 Flask 的 logger
# 或者： logger = logging.getLogger(__name__) # 如果想用模块级 logger，但需确保其处理器已配置

# 允许的文件扩展名 (可以从 src.file_handler 获取，但这里为简化而硬编码)
ALLOWED_EXTENSIONS = {'docx', 'pdf'}

def allowed_file(filename):
    """检查文件名是否具有允许的扩展名。"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """渲染主页 (index.html)。"""
    # 渲染 webapp/templates/index.html 文件
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """
    处理文件上传并将文档转换为 Markdown。
    支持上传多个文件。
    """
    if 'files[]' not in request.files:
        logger.warning("上传请求中没有文件部分 (files[])")
        return jsonify({"error": "请求中没有文件部分 (需要使用 'files[]' 作为字段名)"}), 400

    uploaded_files = request.files.getlist("files[]")

    if not uploaded_files or all(f.filename == '' for f in uploaded_files):
        logger.warning("没有选择任何文件进行上传")
        return jsonify({"error": "没有选择文件"}), 400

    results = []

    for file in uploaded_files:
        if file and file.filename and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            temp_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            
            # original_filename is already secured
            # Save the file to UPLOAD_FOLDER for potential preview and processing
            persistent_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            
            try:
                file.save(persistent_upload_path)
                logger.info(f"文件 '{original_filename}' 已保存到 '{persistent_upload_path}' 供处理和预览。")

                # 调用核心处理逻辑，使用保存的原始文件路径
                markdown_file_path = process_document_to_markdown(persistent_upload_path, app.config['RESULTS_FOLDER'])

                if markdown_file_path:
                    processed_filename = os.path.basename(markdown_file_path)
                    results.append({
                        "original_filename": original_filename, # Keep original for user display
                        "status": "success",
                        "processed_filename": processed_filename, 
                        "message": "文件处理成功"
                    })
                    logger.info(f"文件 '{original_filename}' 处理成功，输出为 '{processed_filename}'")
                else:
                    results.append({
                        "original_filename": original_filename,
                        "status": "error",
                        "message": "文件处理失败 (核心处理器未返回有效路径)"
                    })
                    logger.warning(f"文件 '{original_filename}' 处理失败 (核心处理器返回 None)。")

            except Exception as e:
                logger.error(f"处理文件 '{original_filename}' 时发生严重错误: {e}", exc_info=True)
                results.append({
                    "original_filename": original_filename,
                    "status": "error",
                    "message": f"服务器内部错误: {str(e)}"
                })
            # The original file at persistent_upload_path is intentionally NOT deleted here
            # to make it available for the /preview_docx route.
            # A separate cleanup strategy for the UPLOAD_FOLDER would be needed for long-term deployments.

        elif file and file.filename: # 文件存在但类型不允许
            original_filename = secure_filename(file.filename) # Secure it anyway for logging
            logger.warning(f"文件 '{original_filename}' 的类型不被允许。")
            results.append({
                "original_filename": original_filename,
                "status": "error",
                "message": f"文件类型 '{original_filename.rsplit('.', 1)[1]}' 不受支持。请上传 .docx 或 .pdf 文件。"
            })
        else:
            logger.debug("在上传列表中遇到一个无效的或没有文件名的文件部分。")
            # 可以选择为无效部分添加一个错误条目到 results，或者静默忽略

    return jsonify(results), 200


@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """
    处理文件下载请求。
    从 RESULTS_FOLDER 安全地发送指定的文件。
    """
    logger.info(f"收到下载文件 '{filename}' 的请求。")
    
    # RESULTS_FOLDER 已经是绝对路径或相对于 app.py 的安全路径
    results_dir = app.config['RESULTS_FOLDER']
    
    # 使用 secure_filename 对从 URL 获取的 filename 进行清理是一个好习惯，
    # 尽管 send_from_directory 自身有防目录遍历机制。
    # 但这里要注意，如果原始的 processed_filename 包含在 secure_filename 后会丢失的字符，
    # 可能会导致文件找不到。
    # 假设 upload_files 返回的 processed_filename 是安全的，并且不包含需要 secure_filename 清理的复杂字符。
    # 如果 processed_filename 是直接从用户输入构造的，或者包含路径信息，则必须用 secure_filename。
    # 在当前场景下，processed_filename 是 os.path.basename(markdown_file_path)，应该是安全的。

    try:
        logger.debug(f"尝试从目录 '{results_dir}' 发送文件 '{filename}'。")
        return send_from_directory(results_dir, filename, as_attachment=True)
    except FileNotFoundError:
        logger.error(f"请求下载的文件在服务器上未找到: {os.path.join(results_dir, filename)}")
        return jsonify({"error": "文件未找到"}), 404
    except Exception as e:
        logger.error(f"下载文件 '{filename}' 时发生服务器内部错误: {e}", exc_info=True)
        return jsonify({"error": "服务器内部错误，无法提供文件下载。"}), 500

# Placeholder for mammoth import, will be attempted later
# import mammoth 

@app.route('/preview_docx/<path:filename>')
def preview_docx_file(filename):
    # filename is derived from user input (part of URL), so ensure it's secured
    # although routes with <path:filename> are generally safe from directory traversal by default by Werkzeug,
    # an extra layer of secure_filename is good practice if using it to construct paths directly.
    # However, for this to work, `filename` must match what was stored.
    # If `original_filename` from upload was `secure_filename(file.filename)`, then `filename` here should also be.
    # Let's assume `filename` as received is already the secured version used for saving.
    
    # Construct the full path to the original uploaded .docx file
    original_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(original_file_path):
        logger.error(f"请求预览的 DOCX 文件未找到: {original_file_path}")
        return jsonify({"error": "原始文件未找到，可能已被处理或删除。"}), 404

    if not filename.lower().endswith('.docx'):
        logger.warning(f"请求预览的文件不是 DOCX: {filename}")
        return jsonify({"error": "请求的文件不是 DOCX 格式。"}), 400

    # Attempt to use mammoth first
    try:
        import mammoth # Try importing mammoth
        logger.info(f"尝试使用 mammoth 为 {original_file_path} 生成 HTML 预览。")
        with open(original_file_path, 'rb') as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html_output = result.value 
            if result.messages:
                 logger.warning(f"Mammoth 在转换 {original_file_path} 时产生消息: {result.messages}")
        return jsonify({"html_content": html_output, "library": "mammoth"})
    except ImportError:
        logger.warning("Mammoth 库未安装。尝试使用 pypandoc。")
        # Try pypandoc if mammoth is not available
        try:
            import pypandoc
            logger.info(f"尝试使用 pypandoc 为 {original_file_path} 生成 HTML 预览。")
            # Ensure Pandoc is installed and in PATH for pypandoc to work
            # pypandoc.ensure_pandoc_installed() # This might raise an error or download
            try:
                # Check if pandoc is available by getting its version
                pypandoc.get_pandoc_version()
                logger.info(f"Pandoc version: {pypandoc.get_pandoc_version()} found.")
            except OSError: # Corresponds to pandoc not found
                logger.error("pypandoc 错误：Pandoc 可执行文件未在系统中找到。")
                return jsonify({"error": "服务器错误：Pandoc 未安装或不在 PATH 中，无法进行 DOCX 预览。"}), 500

            html_output = pypandoc.convert_file(original_file_path, 'html5', format='docx')
            return jsonify({"html_content": html_output, "library": "pypandoc"})
        except ImportError:
            logger.error("Pypandoc 库也未安装。无法为 DOCX 生成 HTML 预览。")
            return jsonify({"error": "服务器错误：DOCX 到 HTML 转换库 (Mammoth, Pypandoc) 均不可用。"}), 500
        except Exception as e_pandoc: # Catch errors from pypandoc (e.g., Pandoc conversion error)
            logger.error(f"使用 pypandoc 转换 DOCX {original_file_path} 到 HTML 时发生错误: {e_pandoc}", exc_info=True)
            return jsonify({"error": f"使用 pypandoc 转换 DOCX 到 HTML 失败: {str(e_pandoc)}"}), 500
    except Exception as e_mammoth: # Catch other errors from mammoth
        logger.error(f"使用 mammoth 转换 DOCX {original_file_path} 到 HTML 时发生错误: {e_mammoth}", exc_info=True)
        return jsonify({"error": f"使用 mammoth 转换 DOCX 到 HTML 失败: {str(e_mammoth)}"}), 500


if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true": 
        setup_logging(logging.DEBUG if app.debug else logging.INFO)
    app.run(host='0.0.0.0', port=5000, debug=True)
