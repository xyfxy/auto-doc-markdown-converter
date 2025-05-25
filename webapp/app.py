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
        # 首先使用原始文件名进行类型检查
        if file and file.filename and allowed_file(file.filename):
            # 在确认文件类型允许后，再获取安全的文件名用于保存
            original_filename_for_saving = secure_filename(file.filename)
            # 但日志和后续处理中，我们可能仍想引用用户上传时的原始文件名
            user_original_filename = file.filename # 保留用户上传的原始文件名

            temp_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename_for_saving)
            
            try:
                file.save(temp_upload_path)
                logger.info(f"文件 '{user_original_filename}' (保存为 '{original_filename_for_saving}') 已临时保存到 '{temp_upload_path}'")

                # 调用核心处理逻辑
                markdown_file_path = process_document_to_markdown(temp_upload_path, app.config['RESULTS_FOLDER'])

                if markdown_file_path:
                    processed_filename = os.path.basename(markdown_file_path)
                    results.append({
                        "original_filename": user_original_filename, # 返回给用户的应是原始文件名
                        "status": "success",
                        "processed_filename": processed_filename, # 用于后续下载
                        "message": "文件处理成功"
                    })
                    logger.info(f"文件 '{user_original_filename}' 处理成功，输出为 '{processed_filename}'")
                else:
                    results.append({
                        "original_filename": user_original_filename,
                        "status": "error",
                        "message": "文件处理失败 (核心处理器未返回有效路径，详见服务器日志)"
                    })
                    logger.warning(f"文件 '{user_original_filename}' 处理失败 (核心处理器返回 None)。")

            except Exception as e:
                logger.error(f"处理文件 '{user_original_filename}' 时发生严重错误: {e}", exc_info=True)
                results.append({
                    "original_filename": user_original_filename,
                    "status": "error",
                    "message": f"服务器内部错误: {str(e)}"
                })
            finally:
                # 清理临时上传的文件
                if os.path.exists(temp_upload_path):
                    try:
                        os.remove(temp_upload_path)
                        logger.debug(f"已删除临时上传文件: {temp_upload_path}")
                    except OSError as e_remove:
                        logger.error(f"删除临时文件 {temp_upload_path} 失败: {e_remove}")
        elif file and file.filename: # 文件存在但类型不允许 (基于原始文件名判断)
            user_original_filename = file.filename
            logger.warning(f"文件 '{user_original_filename}' 的类型不被允许。")
            results.append({
                "original_filename": user_original_filename,
                "status": "error",
                "message": f"文件类型 '{user_original_filename.rsplit('.', 1)[1].lower() if '.' in user_original_filename else '未知'}' 不受支持。请上传 .docx 或 .pdf 文件。"
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


if __name__ == '__main__':
    # 为了确保 src 模块中的日志也能按预期工作 (如果它们也使用 logging.getLogger)
    # 我们可以在这里调用 setup_logging 来配置根记录器
    # 这样，即使 Flask 的 app.logger 有自己的配置，其他模块的日志也能输出
    # 注意：如果 setup_logging 改变了根记录器的处理器，可能会影响 Flask 默认的日志行为
    # 一个更稳健的方法可能是获取根记录器并确保其级别和处理器适合开发
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true": # 避免在 Flask 重载时重复配置
        log_level = logging.DEBUG if app.debug else logging.INFO
        # setup_logging(log_level) 
        # 或者，更简单地确保 Flask logger 级别足够低以显示所有信息
        app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
        # 如果 src 模块的日志不显示，则取消注释 setup_logging(log_level)
        # 并确保 setup_logging 不会与 Flask 的日志系统冲突（例如，通过检查处理器是否已存在）
        
        # 临时：为确保 core_processor 等模块的日志能输出，我们调用 setup_logging
        # 这会配置根记录器，Flask 的 app.logger 也会继承这个配置（或被覆盖）
        # 这对于开发调试是可行的，但生产环境需要更精细的日志管理策略
        setup_logging(logging.DEBUG if app.debug else logging.INFO)


    app.run(host='0.0.0.0', port=5000, debug=True)
