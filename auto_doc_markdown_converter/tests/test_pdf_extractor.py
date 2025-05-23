# Placeholder for pdf_extractor tests 

import unittest
import os
import sys

# 将项目根目录添加到 sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.pdf_extractor import extract_text_from_pdf

class TestPdfExtractor(unittest.TestCase):
    """
    测试 PDF 文件文本提取功能。
    """
    def test_extract_text_from_pdf(self):
        """
        测试从 fixtures/sample.pdf 文件提取文本。
        注意：您需要根据实际提取的内容更新下面的 expected_text。
        对于 PDF，精确的文本匹配可能比较困难，可以考虑断言包含关键片段。
        """
        fixture_pdf_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample.pdf')

        # 重要：这是一个占位符。请运行测试，查看打印的"实际提取文本"，
        # 然后用该实际文本（或其关键部分）替换下面的字符串或调整断言逻辑。
        expected_text_placeholder = "请从 fixtures/sample.pdf 的实际提取内容更新此预期文本或断言逻辑。"
        # 对于PDF，由于格式差异，可能更适合检查是否包含某些关键短语
        # expected_keywords = ["某个关键词1", "另一个重要短语"]

        if not os.path.exists(fixture_pdf_path):
            self.fail(f"测试文件未找到: {fixture_pdf_path}，请确保它存在于 fixtures 目录下。")

        extracted_text = extract_text_from_pdf(fixture_pdf_path)
        
        print("\n--- PDF Test (using fixture) ---")
        print(f"测试文件: {fixture_pdf_path}")
        print(f"预期文本 (PDF - 请根据实际内容修改占位符/断言):\n'{expected_text_placeholder}'")
        # print(f"预期应包含的关键词 (PDF): {expected_keywords}") # 如果使用关键词断言
        print(f"实际提取文本 (PDF):\n'{extracted_text}'")
        print("--- End PDF Test ---")
        
        # 初始运行时，此断言很可能会因为 expected_text_placeholder 是占位符而失败。
        # 请在更新 expected_text_placeholder 后，此断言才能正确验证，
        # 或者修改为检查是否包含某些关键词 (assertIn)。
        # 例如: 
        # for keyword in expected_keywords:
        #     self.assertIn(keyword, extracted_text, f"提取的文本中未找到关键词: {keyword}")

        self.assertEqual(extracted_text, expected_text_placeholder, \
                         f"从 PDF 提取的文本与预期不符。请检查 fixtures/sample.pdf 的内容，并更新测试中的 expected_text 或断言逻辑。实际提取内容已打印在上方。")

if __name__ == '__main__':
    unittest.main() 