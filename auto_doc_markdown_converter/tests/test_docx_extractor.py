# Placeholder for docx_extractor tests 

import unittest
import os
import sys

# 将项目根目录添加到 sys.path，以便导入 src 中的模块
# 我们假设 tests 目录与 src 目录在同一级别
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.docx_extractor import extract_text_from_docx

class TestDocxExtractor(unittest.TestCase):
    """
    测试 DOCX 文件文本提取功能。
    """
    def test_extract_text_from_docx(self):
        """
        测试从 fixtures/sample.docx 文件提取文本。
        注意：您需要根据实际提取的内容更新下面的 expected_text。
        """
        fixture_docx_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample.docx')
        
        # 重要：这是一个占位符。请运行测试，查看打印的"实际提取文本"，
        # 然后用该实际文本替换下面的字符串。
        expected_text = "请从 fixtures/sample.docx 的实际提取内容更新此预期文本。"
        # 例如，如果实际提取是 "标题\n内容。"，那么上面就应该是 expected_text = "标题\n内容。"
        
        if not os.path.exists(fixture_docx_path):
            self.fail(f"测试文件未找到: {fixture_docx_path}，请确保它存在于 fixtures 目录下。")

        extracted_text = extract_text_from_docx(fixture_docx_path)
        
        print("\n--- DOCX Test (using fixture) ---")
        print(f"测试文件: {fixture_docx_path}")
        print(f"预期文本 (DOCX - 请根据实际内容修改占位符):\n'{expected_text}'")
        print(f"实际提取文本 (DOCX):\n'{extracted_text}'")
        print("--- End DOCX Test ---")
        
        # 初始运行时，此断言很可能会因为 expected_text 是占位符而失败。
        # 请在更新 expected_text 后，此断言才能正确验证。
        self.assertEqual(extracted_text, expected_text, \
                         f"从 DOCX 提取的文本与预期不符。请检查 fixtures/sample.docx 的内容，并更新测试中的 expected_text。实际提取内容已打印在上方。")

if __name__ == '__main__':
    # 这样可以直接运行此测试文件
    unittest.main() 