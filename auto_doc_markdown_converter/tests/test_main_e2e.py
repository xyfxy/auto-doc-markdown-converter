import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os
import shutil
from pathlib import Path

# 假设的测试装置文件的基本路径
FIXTURES_DIR = Path(__file__).parent / "fixtures"
# 模拟的 LLM 输出
MOCK_LLM_OUTPUT_SIMPLE = "H1: 这是一个简单的标题\nP: 这是一个简单的段落。"
MOCK_LLM_OUTPUT_COMPLEX = "H1: 主标题\nP: 第一段。\nH2: 副标题\nP: 第二段，在副标题下。"
MOCK_LLM_OUTPUT_SPECIAL_CHARS = "H1: 特殊字符标题 éüàñ\nP: 特殊字符段落 “测试”—… éüàñ"

# 辅助函数，用于运行 main.py 脚本
def run_main_script(args_list):
    # 构建命令，确保使用与当前测试环境相同的 Python 解释器
    cmd = [sys.executable, "-m", "auto_doc_markdown_converter.main"] + args_list
    # 使用 text=True 和 encoding='utf-8' 来获取文本输出
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

class TestMainE2E(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """在所有测试开始前运行一次，确保 fixtures 目录存在"""
        if not FIXTURES_DIR.exists():
            # 在真实场景中，如果 fixtures 对测试至关重要，这里应该引发错误或创建目录
            # 对于当前工具的限制，我们假设它由之前的步骤创建
            print(f"警告: Fixtures 目录 {FIXTURES_DIR} 未找到。测试可能依赖于此目录中的文件。")
            # os.makedirs(FIXTURES_DIR, exist_ok=True) # 如果需要动态创建

    def setUp(self):
        """在每个测试用例开始前运行"""
        self.test_input_dir = Path("./test_input_e2e")
        self.test_output_dir = Path("./test_output_e2e")

        # 清理并重新创建测试目录
        if self.test_input_dir.exists():
            shutil.rmtree(self.test_input_dir)
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)
        
        self.test_input_dir.mkdir(parents=True, exist_ok=True)
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

        # 准备测试文件 - 我们将从 fixtures 目录“复制”文件内容
        # 由于我们不能直接操作二进制文件，我们将创建文本文件来代表它们
        self.fixture_files_content = {
            "simple_document.docx": "H1: 简单文档标题\nP: 这是第一个段落。\nH2: 副标题\nP: 这是在副标题下的第二个段落。",
            "simple_document.pdf": "H1: 简单文档标题\nP: 这是第一个段落。\nH2: 副标题\nP: 这是在副标题下的第二个段落。",
            "multi_page_document.docx": "H1: 多页文档第一页标题\nP: 第一页的介绍性段落。\n---PAGEBREAK---\nH1: 多页文档第二页标题\nP: 第二页的开始。",
            "document_with_special_chars.pdf": "H1: 特殊字符测试文档 — “标题”\nP: 这是一个包含特殊字符的段落，例如：中文引号“”，破折号——，省略号…，以及一些非英文字符如 é, ü, à, ñ。"
        }
        
        # 将声明的 fixture 内容写入临时输入目录中的文件
        # 这模拟了从 tests/fixtures 目录复制预定义的 .docx 和 .pdf 文件
        for filename, content in self.fixture_files_content.items():
            with open(self.test_input_dir / filename, "w", encoding="utf-8") as f:
                f.write(content)

    def tearDown(self):
        """在每个测试用例结束后运行"""
        # 清理临时目录
        if self.test_input_dir.exists():
            shutil.rmtree(self.test_input_dir)
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)

    @patch.dict(os.environ, {"LLM_API_KEY": "test_key", "LLM_API_ENDPOINT": "http://fake.endpoint"})
    @patch('auto_doc_markdown_converter.src.llm_processor.analyze_text_with_llm', return_value=MOCK_LLM_OUTPUT_SIMPLE)
    def test_process_single_docx_file(self, mock_analyze_llm):
        """测试处理单个 .docx 文件"""
        input_file = self.test_input_dir / "simple_document.docx"
        
        result = run_main_script([str(input_file), str(self.test_output_dir)])

        # 调试输出
        print(f"测试 'test_process_single_docx_file' STDOUT:\n{result.stdout}")
        print(f"测试 'test_process_single_docx_file' STDERR:\n{result.stderr}")
        
        self.assertEqual(result.returncode, 0, f"脚本执行失败，错误信息: {result.stderr}")
        
        output_md_file = self.test_output_dir / "simple_document.md"
        self.assertTrue(output_md_file.exists(), f"输出 Markdown 文件 {output_md_file} 未创建。")
        
        # 简单的预期 Markdown 输出，基于 MOCK_LLM_OUTPUT_SIMPLE
        # 注意：markdown_generator.generate_markdown_from_labeled_text 的确切输出逻辑
        expected_md_content = "# 这是一个简单的标题\n\n这是一个简单的段落。" 
        
        with open(output_md_file, "r", encoding="utf-8") as f:
            actual_md_content = f.read().strip() # 使用 strip() 移除可能的尾部换行符
        
        self.assertEqual(actual_md_content, expected_md_content, "生成的 Markdown 内容与预期不符。")

        # 验证 llm_processor.analyze_text_with_llm 是否被调用
        # 由于我们直接 mock 了 llm_processor.analyze_text_with_llm，我们需要确认它被调用
        # read_file_content 的 mock 不是此测试的重点，但我们需要确保 analyze_text_with_llm 使用了提取的文本
        # 在这种 E2E 测试风格中，我们信任 read_file_content (或 mock 它以返回特定内容)
        # 这里，我们假设 read_file_content 从我们写入的文本文件中正确读取了内容。
        # 注意：由于 main.py 中 raw_text.strip() 的存在，如果 fixture_files_content 中的内容末尾有换行符，
        # 它们将在调用 analyze_text_with_llm 之前被移除。
        # 为了精确匹配，确保 fixture_files_content 中的字符串与预期传递给 mock 的字符串一致。
        expected_raw_text = self.fixture_files_content["simple_document.docx"].strip()
        mock_analyze_llm.assert_called_once_with(expected_raw_text)

    @patch.dict(os.environ, {"LLM_API_KEY": "test_key", "LLM_API_ENDPOINT": "http://fake.endpoint"})
    @patch('auto_doc_markdown_converter.src.llm_processor.analyze_text_with_llm', return_value=MOCK_LLM_OUTPUT_SIMPLE)
    def test_process_single_pdf_file(self, mock_analyze_llm):
        """测试处理单个 .pdf 文件"""
        input_file = self.test_input_dir / "simple_document.pdf"
        
        result = run_main_script([str(input_file), str(self.test_output_dir)])

        print(f"测试 'test_process_single_pdf_file' STDOUT:\n{result.stdout}")
        print(f"测试 'test_process_single_pdf_file' STDERR:\n{result.stderr}")

        self.assertEqual(result.returncode, 0, f"脚本执行失败，错误信息: {result.stderr}")
        
        output_md_file = self.test_output_dir / "simple_document.md"
        self.assertTrue(output_md_file.exists(), f"输出 Markdown 文件 {output_md_file} 未创建。")
        
        expected_md_content = "# 这是一个简单的标题\n\n这是一个简单的段落。"
        with open(output_md_file, "r", encoding="utf-8") as f:
            actual_md_content = f.read().strip()
        self.assertEqual(actual_md_content, expected_md_content, "生成的 Markdown 内容与预期不符。")
        
        expected_raw_text = self.fixture_files_content["simple_document.pdf"].strip()
        mock_analyze_llm.assert_called_once_with(expected_raw_text)

    @patch.dict(os.environ, {"LLM_API_KEY": "test_key", "LLM_API_ENDPOINT": "http://fake.endpoint"})
    @patch('auto_doc_markdown_converter.src.llm_processor.analyze_text_with_llm')
    def test_process_directory(self, mock_analyze_llm):
        """测试处理整个目录"""
        # 定义 mock_analyze_llm 如何根据输入文本返回不同的输出
        def side_effect_function(text_input):
            if text_input == self.fixture_files_content["simple_document.docx"].strip():
                return MOCK_LLM_OUTPUT_SIMPLE
            elif text_input == self.fixture_files_content["multi_page_document.docx"].strip():
                return MOCK_LLM_OUTPUT_COMPLEX
            elif text_input == self.fixture_files_content["document_with_special_chars.pdf"].strip():
                return MOCK_LLM_OUTPUT_SPECIAL_CHARS
            return "H1: 默认标题\nP: 默认段落。" # 以防万一
        
        mock_analyze_llm.side_effect = side_effect_function

        # 在输入目录中创建多个文件
        # simple_document.docx 和 document_with_special_chars.pdf 已在 setUp 中创建
        # 我们需要确保 multi_page_document.docx 也在那里
        # (setUp 中已包含 multi_page_document.docx)

        result = run_main_script([str(self.test_input_dir), str(self.test_output_dir)])

        print(f"测试 'test_process_directory' STDOUT:\n{result.stdout}")
        print(f"测试 'test_process_directory' STDERR:\n{result.stderr}")

        self.assertEqual(result.returncode, 0, f"脚本执行失败，错误信息: {result.stderr}")

        # 检查是否为每个输入文件都生成了对应的 .md 文件
        expected_outputs = {
            "simple_document.md": MOCK_LLM_OUTPUT_SIMPLE,
            "multi_page_document.md": MOCK_LLM_OUTPUT_COMPLEX,
            "document_with_special_chars.md": MOCK_LLM_OUTPUT_SPECIAL_CHARS,
            "simple_document.pdf.md": MOCK_LLM_OUTPUT_SIMPLE # simple_document.pdf 的输出也用 MOCK_LLM_OUTPUT_SIMPLE
        }
        # 注意：由于 simple_document.pdf 的内容与 simple_document.docx 相同，
        # 并且 side_effect_function 没有为 simple_document.pdf 的内容区分，
        # 它将回退到 "默认标题/段落" 或与 simple_document.docx 相同的输出，
        # 取决于 self.fixture_files_content["simple_document.pdf"].strip() 是否等于 self.fixture_files_content["simple_document.docx"].strip()
        # 为了测试的明确性，我们调整 side_effect_function 或 fixture 内容
        # 假设 simple_document.pdf 的内容与 docx 不同，或者为其添加特定的 mock 输出
        # 为了简化，我们这里让 simple_document.pdf 也使用 MOCK_LLM_OUTPUT_SIMPLE，
        # 需要确保 side_effect_function 能正确处理这种情况（通过比较其内容）。
        # 当前 fixture_files_content 中 simple_document.pdf 和 simple_document.docx 内容相同。

        # 修正：确保 side_effect_function 能区分它们，或者接受它们有相同的 mock 输出
        # 在当前的 fixture_files_content 定义中，它们的内容是一样的，所以 mock_analyze_llm 会为两者返回 MOCK_LLM_OUTPUT_SIMPLE
        # 所以，simple_document.pdf.md 应该不存在，而是 simple_document.md (来自 pdf)
        # main.py 中对 .pdf 文件的输出命名是 <stem>.md，所以 simple_document.pdf 会输出 simple_document.md
        # 这会导致文件名冲突，如果目录中有 simple_document.docx 和 simple_document.pdf
        # 根据 main.py 的逻辑，后处理的文件会覆盖先处理的。
        # 为了避免歧义，我们应该在 setUp 中使用不同的文件名，或者接受覆盖。
        # 我们将测试 simple_document.md 和 multi_page_document.md。
        # document_with_special_chars.pdf -> document_with_special_chars.md

        files_in_input_dir = [f for f in self.test_input_dir.iterdir() if f.is_file()]
        self.assertGreater(len(files_in_input_dir), 1, "测试目录中应有多个文件")


        for input_file_path in files_in_input_dir:
            output_filename = input_file_path.stem + ".md"
            output_md_file = self.test_output_dir / output_filename
            self.assertTrue(output_md_file.exists(), f"输出 Markdown 文件 {output_md_file} 未为输入文件 {input_file_path.name} 创建。")

            # 检查内容
            if output_filename == "simple_document.md":
                # 这个文件可能被 .docx 或 .pdf 版本覆盖，内容应为 MOCK_LLM_OUTPUT_SIMPLE
                expected_md_content = "# 这是一个简单的标题\n\n这是一个简单的段落。"
            elif output_filename == "multi_page_document.md":
                expected_md_content = "# 主标题\n\n第一段。\n\n## 副标题\n\n第二段，在副标题下。"
            elif output_filename == "document_with_special_chars.md":
                expected_md_content = "# 特殊字符标题 éüàñ\n\n特殊字符段落 “测试”—… éüàñ"
            else:
                # 对于此测试设置中未明确映射的其他文件，我们不严格检查内容，只检查存在性
                print(f"警告: 未对 {output_filename} 的内容进行特定断言。")
                continue
            
            with open(output_md_file, "r", encoding="utf-8") as f:
                actual_md_content = f.read().strip()
            self.assertEqual(actual_md_content, expected_md_content, f"文件 {output_md_file} 的内容与预期不符。")
        
        # 验证 mock_analyze_llm 被调用了正确的次数
        self.assertEqual(mock_analyze_llm.call_count, len(files_in_input_dir), "analyze_text_with_llm 调用次数与输入文件数不符。")


    @patch.dict(os.environ, {"LLM_API_KEY": "test_key", "LLM_API_ENDPOINT": "http://fake.endpoint"})
    def test_input_file_not_found(self, mock_analyze_llm_dummy=None): # mock_analyze_llm_dummy 用于捕获可能的调用，但不在此测试中使用
        """测试输入文件未找到的情况"""
        non_existent_file = self.test_input_dir / "non_existent_file.docx"
        
        result = run_main_script([str(non_existent_file), str(self.test_output_dir)])

        print(f"测试 'test_input_file_not_found' STDOUT:\n{result.stdout}")
        print(f"测试 'test_input_file_not_found' STDERR:\n{result.stderr}")
        
        self.assertNotEqual(result.returncode, 0, "脚本在输入文件未找到时应返回非零退出码。")
        # 检查 stderr 是否包含预期的错误信息 (这取决于 main.py 中的日志/错误输出)
        # 例如: self.assertIn("输入路径不存在", result.stderr) # 或 result.stdout，取决于日志配置
        # 由于日志现在会输出到 stdout (INFO) 或 stderr (ERROR, CRITICAL)
        # "输入路径不存在" 是 logger.error，所以应该在 stderr
        self.assertIn(f"输入路径不存在: {non_existent_file}", result.stdout, "预期的 '输入路径不存在' 错误信息未在 stdout 中找到。")


    @patch.dict(os.environ, {"LLM_API_KEY": "test_key", "LLM_API_ENDPOINT": "http://fake.endpoint"})
    @patch('auto_doc_markdown_converter.src.llm_processor.analyze_text_with_llm', return_value=MOCK_LLM_OUTPUT_SIMPLE)
    def test_verbose_option(self, mock_analyze_llm):
        """测试 --verbose 选项"""
        input_file = self.test_input_dir / "simple_document.docx"
        
        result = run_main_script([str(input_file), str(self.test_output_dir), "--verbose"])

        print(f"测试 'test_verbose_option' STDOUT:\n{result.stdout}")
        print(f"测试 'test_verbose_option' STDERR:\n{result.stderr}")

        self.assertEqual(result.returncode, 0, f"脚本使用 --verbose 选项执行失败，错误信息: {result.stderr}")
        
        # 检查 stdout 是否包含 DEBUG 级别的日志 (这取决于 setup_logging 和 main.py 中的具体日志消息)
        # 例如，main.py 中有 logger.debug("正在执行初始检查...")
        self.assertIn("DEBUG: 正在执行初始检查...", result.stdout, "启用 --verbose 时，stdout 中应包含 DEBUG 级别的日志。")
        
        output_md_file = self.test_output_dir / "simple_document.md"
        self.assertTrue(output_md_file.exists(), "输出 Markdown 文件未在 --verbose 模式下创建。")


# 运行测试 (如果直接执行此文件)
if __name__ == '__main__':
    unittest.main()
