import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock, call # 确保导入 call
import logging

# 确保项目根目录在 sys.path 中，以便导入 src 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from auto_doc_markdown_converter.src.core_processor import process_document_to_markdown
from auto_doc_markdown_converter.src.text_splitter import DEFAULT_MAX_CHUNK_TOKENS, DEFAULT_OVERLAP_TOKENS
# from auto_doc_markdown_converter.src import config as core_config # 不再需要，因为MAX_TOKENS_FOR_DIRECT_PROCESSING在core_processor中

# 配置一个临时的测试日志记录器，避免在测试输出中看到过多的 INFO 日志
# 如果需要查看测试过程中的详细日志，可以调整这里的级别
# logging.basicConfig(level=logging.DEBUG) # 打开此行以查看详细日志
# logging.getLogger('auto_doc_markdown_converter.src.core_processor').setLevel(logging.DEBUG)


class TestCoreProcessorLongText(unittest.TestCase):
    """
    测试 core_processor.py 中的 process_document_to_markdown 函数，
    特别是针对长文本处理逻辑的集成测试。
    """

    def setUp(self):
        """在每个测试用例开始前运行"""
        # 设置必要的环境变量的 mock 值
        self.env_patcher_key = patch.dict(os.environ, {"LLM_API_KEY": "test_api_key"})
        self.env_patcher_endpoint = patch.dict(os.environ, {"LLM_API_ENDPOINT": "http://mock.endpoint"})
        self.env_patcher_model = patch.dict(os.environ, {"LLM_MODEL_ID": "test_model_for_core_tests"}) # 使用特定模型ID
        self.env_patcher_timeout = patch.dict(os.environ, {"LLM_API_CALL_TIMEOUT": "10"}) 

        self.env_patcher_key.start()
        self.env_patcher_endpoint.start()
        self.env_patcher_model.start()
        self.env_patcher_timeout.start()
        
        self.test_results_dir = "test_core_processor_results_dir" # 确保目录名独特
        # 使用 patch 来 mock os.makedirs，避免实际创建目录
        self.mock_os_makedirs = patch('auto_doc_markdown_converter.src.core_processor.os.makedirs').start()
        
        # MAX_TOKENS_FOR_DIRECT_PROCESSING 是在 core_processor 模块级别从 text_splitter 导入并赋值的。
        # 为了在测试中控制这个阈值，我们需要 patch 它在 core_processor 模块中的引用。
        # 如果 core_processor.py 是: from .text_splitter import DEFAULT_MAX_CHUNK_TOKENS as MAX_TOKENS_FOR_DIRECT_PROCESSING
        # 或者 MAX_TOKENS_FOR_DIRECT_PROCESSING = some_value
        # 我们可以直接patch 'auto_doc_markdown_converter.src.core_processor.MAX_TOKENS_FOR_DIRECT_PROCESSING'
        # 假设 core_processor.MAX_TOKENS_FOR_DIRECT_PROCESSING 可以被 patch
        self.mock_threshold_val = 50 # 用于测试的阈值
        self.patcher_max_tokens_threshold = patch('auto_doc_markdown_converter.src.core_processor.MAX_TOKENS_FOR_DIRECT_PROCESSING', self.mock_threshold_val)
        self.patcher_max_tokens_threshold.start()


    def tearDown(self):
        """在每个测试用例结束后运行"""
        self.env_patcher_key.stop()
        self.env_patcher_endpoint.stop()
        self.env_patcher_model.stop()
        self.env_patcher_timeout.stop()
        self.patcher_max_tokens_threshold.stop()
        patch.stopall() # 停止所有由 @patch 或 patch.start() 启动的 patchers

        # 清理测试目录中的文件（如果实际创建了）
        if os.path.exists(self.test_results_dir):
            for f_name in os.listdir(self.test_results_dir):
                os.remove(os.path.join(self.test_results_dir, f_name))
            # os.rmdir(self.test_results_dir) # 如果测试后确定目录为空，可以移除


    @patch('builtins.open', new_callable=mock_open)
    @patch('auto_doc_markdown_converter.src.core_processor.generate_markdown_from_labeled_text', return_value="## Markdown Content")
    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks') 
    @patch('auto_doc_markdown_converter.src.core_processor.merge_processed_chunks') 
    @patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
    @patch('auto_doc_markdown_converter.src.core_processor.read_file_content', return_value="Short raw text.")
    @patch('auto_doc_markdown_converter.src.core_processor.get_file_type', return_value='docx')
    def test_short_text_direct_processing(self, mock_get_file_type, mock_read_content, 
                                          mock_estimate_tokens, mock_merge_chunks, 
                                          mock_split_chunks, mock_analyze_llm, 
                                          mock_generate_md, mock_file_open):
        """测试短文本（token 数低于阈值）时，直接调用 LLM 进行处理。"""
        mock_estimate_tokens.return_value = self.mock_threshold_val -1 # 确保小于阈值
        mock_analyze_llm.return_value = "P: Short LLM output."
        
        input_file = "dummy_short.docx"
        result_path = process_document_to_markdown(input_file, self.test_results_dir)

        mock_read_content.assert_called_once_with(input_file, 'docx')
        # estimate_tokens 会被调用一次来判断是否为长文本
        mock_estimate_tokens.assert_called_once_with("Short raw text.", model_name="test_model_for_core_tests")
        mock_analyze_llm.assert_called_once_with("Short raw text.")
        mock_split_chunks.assert_not_called() # 不应调用分块
        mock_merge_chunks.assert_not_called() # 不应调用合并
        mock_generate_md.assert_called_once_with("P: Short LLM output.")
        
        expected_output_filename = os.path.splitext(os.path.basename(input_file))[0] + ".md"
        expected_path = os.path.join(self.test_results_dir, expected_output_filename)
        self.assertEqual(result_path, expected_path)
        self.mock_os_makedirs.assert_called_once_with(self.test_results_dir, exist_ok=True)
        mock_file_open.assert_called_once_with(expected_path, "w", encoding="utf-8")
        mock_file_open().write.assert_called_once_with("## Markdown Content")


    @patch('builtins.open', new_callable=mock_open)
    @patch('auto_doc_markdown_converter.src.core_processor.generate_markdown_from_labeled_text', return_value="## Merged Markdown")
    @patch('auto_doc_markdown_converter.src.core_processor.merge_processed_chunks')
    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks')
    @patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
    @patch('auto_doc_markdown_converter.src.core_processor.read_file_content', return_value="Long raw text " * 100) # 确保文本足够长
    @patch('auto_doc_markdown_converter.src.core_processor.get_file_type', return_value='pdf')
    def test_long_text_chunk_processing_success(self, mock_get_file_type, mock_read_content,
                                                mock_estimate_tokens, mock_split_chunks,
                                                mock_analyze_llm, mock_merge_chunks,
                                                mock_generate_md, mock_file_open):
        """测试长文本（token 数超过阈值）成功进行分块处理、LLM分析、合并和Markdown生成。"""
        long_text_content = "Long raw text " * 100
        mock_read_content.return_value = long_text_content
        mock_estimate_tokens.return_value = self.mock_threshold_val + 100 # 确保大于阈值
        
        raw_chunks = ["chunk1_raw", "chunk2_raw", "chunk3_raw"]
        mock_split_chunks.return_value = raw_chunks
        
        processed_llm_chunks = ["P: chunk1_processed", "P: chunk2_processed", "P: chunk3_processed"]
        mock_analyze_llm.side_effect = processed_llm_chunks
        
        mock_merge_chunks.return_value = "P: Merged LLM output from multiple chunks."

        input_file = "dummy_long_success.pdf"
        result_path = process_document_to_markdown(input_file, self.test_results_dir)

        mock_estimate_tokens.assert_called_once_with(long_text_content, model_name="test_model_for_core_tests")
        mock_split_chunks.assert_called_once_with(
            long_text_content,
            model_name="test_model_for_core_tests",
            max_tokens_per_chunk=DEFAULT_MAX_CHUNK_TOKENS, 
            overlap_tokens=DEFAULT_OVERLAP_TOKENS
        )
        self.assertEqual(mock_analyze_llm.call_count, len(raw_chunks))
        mock_analyze_llm.assert_has_calls([call(c) for c in raw_chunks])
        mock_merge_chunks.assert_called_once_with(
            processed_llm_chunks,
            raw_chunks, 
            overlap_tokens=DEFAULT_OVERLAP_TOKENS,
            model_name="test_model_for_core_tests"
        )
        mock_generate_md.assert_called_once_with("P: Merged LLM output from multiple chunks.")
        
        expected_output_filename = os.path.splitext(os.path.basename(input_file))[0] + ".md"
        expected_path = os.path.join(self.test_results_dir, expected_output_filename)
        self.assertEqual(result_path, expected_path)
        mock_file_open.assert_called_once_with(expected_path, "w", encoding="utf-8")
        mock_file_open().write.assert_called_once_with("## Merged Markdown")

    @patch('auto_doc_markdown_converter.src.core_processor.generate_markdown_from_labeled_text') 
    @patch('auto_doc_markdown_converter.src.core_processor.merge_processed_chunks') 
    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks')
    @patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
    @patch('auto_doc_markdown_converter.src.core_processor.read_file_content', return_value="Long text for LLM chunk failure.")
    @patch('auto_doc_markdown_converter.src.core_processor.get_file_type', return_value='docx')
    def test_long_text_llm_fail_on_one_chunk(self, mock_get_file_type, mock_read_content,
                                             mock_estimate_tokens, mock_split_chunks,
                                             mock_analyze_llm, mock_merge_chunks,
                                             mock_generate_md):
        """测试长文本处理时，如果任意一个块的LLM分析失败，则整个处理返回None。"""
        mock_estimate_tokens.return_value = self.mock_threshold_val + 100
        mock_split_chunks.return_value = ["chunk1_raw", "chunk2_raw_fails", "chunk3_raw"]
        # 第二个块LLM处理返回None
        mock_analyze_llm.side_effect = ["P: chunk1_processed", None, "P: chunk3_processed"] 

        input_file = "dummy_llm_fail_chunk.docx"
        result_path = process_document_to_markdown(input_file, self.test_results_dir)

        self.assertIsNone(result_path, "当一个块LLM分析失败时，应返回None")
        mock_split_chunks.assert_called_once()
        # analyze_text_with_llm 应该被调用直到失败的那个块
        self.assertEqual(mock_analyze_llm.call_count, 2) 
        mock_analyze_llm.assert_any_call("chunk1_raw")
        mock_analyze_llm.assert_any_call("chunk2_raw_fails")
        mock_merge_chunks.assert_not_called() # 因为LLM分析中途失败
        mock_generate_md.assert_not_called()


    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks', return_value=None) # 分割失败返回 None
    @patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
    @patch('auto_doc_markdown_converter.src.core_processor.read_file_content', return_value="Long text for split failure (None).")
    @patch('auto_doc_markdown_converter.src.core_processor.get_file_type', return_value='docx')
    def test_long_text_split_fails_returns_none(self, mock_get_file_type, mock_read_content,
                                           mock_estimate_tokens, mock_split_chunks, mock_analyze_llm):
        """测试长文本分割失败（split_text_into_chunks返回None）时，整个处理返回None。"""
        mock_estimate_tokens.return_value = self.mock_threshold_val + 100
        
        input_file = "dummy_split_fail_none.docx"
        result_path = process_document_to_markdown(input_file, self.test_results_dir)

        self.assertIsNone(result_path, "当文本分割返回None时，应返回None")
        mock_split_chunks.assert_called_once()
        mock_analyze_llm.assert_not_called()


    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks', return_value=[]) # 分割失败返回空列表
    @patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
    @patch('auto_doc_markdown_converter.src.core_processor.read_file_content', return_value="Long text for split failure (empty list).")
    @patch('auto_doc_markdown_converter.src.core_processor.get_file_type', return_value='docx')
    def test_long_text_split_fails_returns_empty_list(self, mock_get_file_type, mock_read_content,
                                           mock_estimate_tokens, mock_split_chunks, mock_analyze_llm):
        """测试长文本分割失败（split_text_into_chunks返回空列表）时，整个处理返回None。"""
        mock_estimate_tokens.return_value = self.mock_threshold_val + 100
        
        input_file = "dummy_split_fail_empty.docx"
        result_path = process_document_to_markdown(input_file, self.test_results_dir)

        self.assertIsNone(result_path, "当文本分割返回空列表时，应返回None")
        mock_split_chunks.assert_called_once()
        mock_analyze_llm.assert_not_called()


    @patch('auto_doc_markdown_converter.src.core_processor.generate_markdown_from_labeled_text') 
    @patch('auto_doc_markdown_converter.src.core_processor.merge_processed_chunks', return_value=None) # 合并失败返回 None
    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks')
    @patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
    @patch('auto_doc_markdown_converter.src.core_processor.read_file_content', return_value="Long text for merge failure (None).")
    @patch('auto_doc_markdown_converter.src.core_processor.get_file_type', return_value='docx')
    def test_long_text_merge_fails_returns_none(self, mock_get_file_type, mock_read_content,
                                            mock_estimate_tokens, mock_split_chunks,
                                            mock_analyze_llm, mock_merge_chunks,
                                            mock_generate_md):
        """测试长文本合并结果失败（merge_processed_chunks返回None）时，整个处理返回None。"""
        mock_estimate_tokens.return_value = self.mock_threshold_val + 100
        mock_split_chunks.return_value = ["chunk1_raw", "chunk2_raw"]
        mock_analyze_llm.side_effect = ["P: chunk1_processed", "P: chunk2_processed"]
        
        input_file = "dummy_merge_fail_none.docx"
        result_path = process_document_to_markdown(input_file, self.test_results_dir)

        self.assertIsNone(result_path, "当结果合并返回None时，应返回None")
        mock_merge_chunks.assert_called_once()
        mock_generate_md.assert_not_called() # 因为合并结果为None


    @patch('auto_doc_markdown_converter.src.core_processor.generate_markdown_from_labeled_text', return_value=None) # 假设Markdown生成也可能因空输入而失败
    @patch('auto_doc_markdown_converter.src.core_processor.merge_processed_chunks', return_value="  ") # 合并返回空白字符串
    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks')
    @patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
    @patch('auto_doc_markdown_converter.src.core_processor.read_file_content', return_value="Long text for merge failure (empty str).")
    @patch('auto_doc_markdown_converter.src.core_processor.get_file_type', return_value='docx')
    def test_long_text_merge_fails_returns_empty_str(self, mock_get_file_type, mock_read_content,
                                            mock_estimate_tokens, mock_split_chunks,
                                            mock_analyze_llm, mock_merge_chunks,
                                            mock_generate_md):
        """测试长文本合并结果失败（返回空白字符串）时，整个处理返回None。"""
        mock_estimate_tokens.return_value = self.mock_threshold_val + 100
        mock_split_chunks.return_value = ["chunk1_raw", "chunk2_raw"]
        mock_analyze_llm.side_effect = ["P: chunk1_processed", "P: chunk2_processed"]
        
        input_file = "dummy_merge_fail_empty_str.docx"
        result_path = process_document_to_markdown(input_file, self.test_results_dir)

        self.assertIsNone(result_path, "当结果合并返回空白字符串且Markdown生成也失败时，应返回None") 
        mock_merge_chunks.assert_called_once()
        # generate_markdown_from_labeled_text 会被调用，但其返回 None (或空白) 导致最终结果为 None
        mock_generate_md.assert_called_once_with("  ")


if __name__ == '__main__':
    unittest.main()
