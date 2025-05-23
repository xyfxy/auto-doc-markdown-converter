import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import io
import json
import sys
from flask import Flask, Response # Response 用于 test_download_file_success

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from webapp.app import app # 导入 Flask 应用实例

class TestAppRoutes(unittest.TestCase):

    def setUp(self):
        """在每个测试用例开始前运行"""
        app.testing = True  # 开启测试模式
        self.client = app.test_client() # 创建测试客户端

        # 设置测试用的 UPLOAD_FOLDER 和 RESULTS_FOLDER
        # 这些路径将在测试期间由 Flask 应用实例使用
        # 注意：app.config['UPLOAD_FOLDER'] 和 app.config['RESULTS_FOLDER']
        # 已经在 webapp.app 模块加载时被 os.path.join(BASE_DIR, 'uploads') 等方式设置。
        # 我们这里可以覆盖它们为临时测试目录，或者依赖于它们是相对路径并在测试运行时是可写的。
        # 为了测试的隔离性，最好使用临时目录，但这里我们遵循原始 app.py 的设置，
        # 并假设这些目录（webapp/uploads, webapp/results）在测试环境中是可访问的。
        # 如果测试涉及到实际的文件写入（例如，不 mock process_document_to_markdown），
        # 则需要确保这些目录在测试前后被正确管理（创建/清理）。
        # 当前的测试策略是 mock 掉会产生副作用的函数，所以实际文件写入不多。

        # 确保环境变量已设置 (对于核心处理器中的检查)
        # 这些值可以是 mock 值，因为实际的 LLM 调用会被 mock
        os.environ['LLM_API_KEY'] = 'test_mock_api_key'
        os.environ['LLM_API_ENDPOINT'] = 'http://mock.test.endpoint'
        os.environ['LLM_MODEL_ID'] = 'test-model'


    def tearDown(self):
        """在每个测试用例结束后运行"""
        # 清理可能在测试中创建的环境变量
        del os.environ['LLM_API_KEY']
        del os.environ['LLM_API_ENDPOINT']
        del os.environ['LLM_MODEL_ID']
        # 如果测试中创建了临时文件/目录，在此处清理

    def test_index_route(self):
        """测试根路径 (/) 是否成功渲染 index.html"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'智能文档清洗与 Markdown 转换工具', response.data) # 检查 HTML 内容
        self.assertIn(b'选择文件 (可多选)', response.data)

    @patch('webapp.app.process_document_to_markdown') # Mock 核心处理函数
    def test_upload_single_docx_file_success(self, mock_process_document):
        """测试成功上传单个 .docx 文件"""
        # 配置 mock_process_document 的返回值
        mock_md_filename = 'test_doc.md'
        # 确保返回的是一个完整的模拟路径，或者仅是文件名，取决于 app.py 中如何使用它
        # app.py 中的 os.path.basename(markdown_file_path) 会提取文件名
        mock_process_document.return_value = os.path.join(app.config['RESULTS_FOLDER'], mock_md_filename)

        data = {
            'files[]': (io.BytesIO(b"dummy docx content"), 'test_doc.docx')
        }
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(response_json, list)
        self.assertEqual(len(response_json), 1)
        self.assertEqual(response_json[0]['original_filename'], 'test_doc.docx')
        self.assertEqual(response_json[0]['status'], 'success')
        self.assertEqual(response_json[0]['processed_filename'], mock_md_filename)
        
        # 验证 mock_process_document 被正确调用
        args, kwargs = mock_process_document.call_args
        actual_temp_upload_path = args[0] 
        self.assertTrue(actual_temp_upload_path.startswith(app.config['UPLOAD_FOLDER']))
        self.assertTrue(actual_temp_upload_path.endswith('test_doc.docx')) 
        self.assertEqual(args[1], app.config['RESULTS_FOLDER'])

    @patch('webapp.app.process_document_to_markdown')
    def test_upload_multiple_files_success(self, mock_process_document):
        """测试成功上传多个文件 (.docx, .pdf)"""
        def side_effect_func(input_path, results_dir):
            filename = os.path.basename(input_path)
            # 模拟 process_document_to_markdown 返回的是完整路径
            return os.path.join(results_dir, filename.replace('.docx', '.md').replace('.pdf', '.md'))
        
        mock_process_document.side_effect = side_effect_func

        data = {
            'files[]': [
                (io.BytesIO(b"docx content"), 'doc1.docx'),
                (io.BytesIO(b"pdf content"), 'doc2.pdf')
            ]
        }
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(response_json), 2)

        # 检查第一个文件的结果
        self.assertEqual(response_json[0]['original_filename'], 'doc1.docx')
        self.assertEqual(response_json[0]['status'], 'success')
        self.assertEqual(response_json[0]['processed_filename'], 'doc1.md')
        
        # 检查第二个文件的结果
        self.assertEqual(response_json[1]['original_filename'], 'doc2.pdf')
        self.assertEqual(response_json[1]['status'], 'success')
        self.assertEqual(response_json[1]['processed_filename'], 'doc2.md')

        # 验证 mock 调用次数
        self.assertEqual(mock_process_document.call_count, 2)


    @patch('webapp.app.process_document_to_markdown') 
    def test_upload_unsupported_file_type(self, mock_process_document):
        """测试上传不支持的文件类型"""
        data = {'files[]': (io.BytesIO(b"text content"), 'test.txt')}
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 200) 
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(response_json), 1)
        self.assertEqual(response_json[0]['original_filename'], 'test.txt')
        self.assertEqual(response_json[0]['status'], 'error')
        self.assertIn("文件类型 '.txt' 不受支持", response_json[0]['message']) # 确保与 app.py 中的错误信息一致
        mock_process_document.assert_not_called() 

    def test_upload_no_files_field(self):
        """测试上传请求中没有 'files[]' 字段的情况"""
        # 发送一个空的 data，或者 data 中不包含 'files[]'
        response = self.client.post('/upload', content_type='multipart/form-data', data={})
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], "请求中没有文件部分 (需要使用 'files[]' 作为字段名)")

    def test_upload_empty_file_list(self):
        """测试 'files[]' 字段存在但没有选择文件的情况"""
        # Flask/Werkzeug 处理空文件列表的方式可能是在 request.files 中不包含该键，
        # 或者 getlist 返回空列表。 app.py 中的逻辑是先检查 'files[]' not in request.files，
        # 然后检查 uploaded_files 是否为空。
        # 我们直接发送一个空的 files[] 列表（通过 werkzeug 的 FileStorage 模拟比较复杂，
        # 但可以通过发送一个没有实际文件数据的 multipart 请求来间接触发）
        # 或者，更简单地，测试 app.py 中 `if not uploaded_files or all(f.filename == '' for f in uploaded_files):` 这条路径
        # 通过发送一个包含空文件名的文件字段
        data = {'files[]': (io.BytesIO(b""), '')} # 文件名为空
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], "没有选择文件")


    @patch('webapp.app.process_document_to_markdown', return_value=None)
    def test_upload_processing_fails(self, mock_process_document):
        """测试核心处理函数 process_document_to_markdown 返回 None (处理失败)"""
        data = {'files[]': (io.BytesIO(b"docx content"), 'fail_doc.docx')}
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(response_json), 1)
        self.assertEqual(response_json[0]['status'], 'error')
        self.assertIn('文件处理失败', response_json[0]['message'])

    @patch('webapp.app.send_from_directory') 
    def test_download_file_success(self, mock_send_from_directory):
        """测试成功下载文件"""
        mock_send_from_directory.return_value = Response("dummy md content", mimetype='text/markdown')

        filename = 'test_doc.md'
        response = self.client.get(f'/download/{filename}')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"dummy md content")
        self.assertEqual(response.mimetype, 'text/markdown')
        mock_send_from_directory.assert_called_once_with(
            app.config['RESULTS_FOLDER'], filename, as_attachment=True
        )

    # 这个测试依赖于 send_from_directory 的实际行为
    def test_download_file_not_found(self):
        """测试请求下载一个不存在的文件"""
        non_existent_file = 'no_such_file_ever.md'
        # 确保文件真的不存在于测试的 RESULTS_FOLDER
        # (通常 setUp 会清理，或者我们可以选择一个几乎不可能存在的文件名)
        file_path_to_check = os.path.join(app.config['RESULTS_FOLDER'], non_existent_file)
        if os.path.exists(file_path_to_check):
            os.remove(file_path_to_check) # 以防万一

        response = self.client.get(f'/download/{non_existent_file}')
        self.assertEqual(response.status_code, 404) 
        # Flask 的 send_from_directory 在找不到文件时会正确地 abort(404)
        # 默认的 404 页面是 HTML，所以不检查 JSON
        self.assertIn(b'404 Not Found', response.data) # 检查是否是标准的 404 页面内容

if __name__ == '__main__':
    unittest.main()
