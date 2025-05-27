import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import shutil # For managing temporary directories
import logging

# 将项目根目录添加到 sys.path
# This assumes tests are run from the project root or this path adjustment works.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# print(f"TestPdfExtractor: sys.path updated with {project_root}")
# print(f"TestPdfExtractor: Current sys.path: {sys.path}")

from auto_doc_markdown_converter.src.pdf_extractor import extract_content_from_pdf

# Disable logging for most tests to keep output clean, can be enabled for debugging
logging.disable(logging.CRITICAL)

class TestPdfContentExtractor(unittest.TestCase):
    """
    Test suite for extract_content_from_pdf function in pdf_extractor.py.
    Relies heavily on mocking external PDF libraries (fitz, pdfplumber).
    """

    def setUp(self):
        """Set up a temporary directory for test results."""
        self.test_results_dir = os.path.join(os.path.dirname(__file__), "temp_test_results")
        os.makedirs(self.test_results_dir, exist_ok=True)
        # self.images_sub_dir = os.path.join(self.test_results_dir, 'images') # pdf_extractor creates this

        # Define paths to conceptual fixture files.
        # These files don't need to exist with actual complex content if we are mocking library calls.
        self.fixture_base_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.mock_pdf_simple_text = os.path.join(self.fixture_base_path, 'simple_document.pdf') # Assume this exists for path validity
        self.mock_pdf_with_image = os.path.join(self.fixture_base_path, 'mock_pdf_with_image.pdf')
        self.mock_pdf_with_table = os.path.join(self.fixture_base_path, 'mock_pdf_with_table.pdf')
        self.mock_pdf_with_image_and_table = os.path.join(self.fixture_base_path, 'mock_pdf_image_table.pdf')
        self.mock_blank_pdf = os.path.join(self.fixture_base_path, 'mock_blank.pdf')
        self.corrupted_pdf_path = os.path.join(self.fixture_base_path, 'corrupted.pdf') # This one should exist (0-byte)


    def tearDown(self):
        """Remove the temporary directory after tests."""
        if os.path.exists(self.test_results_dir):
            shutil.rmtree(self.test_results_dir)

    @patch('auto_doc_markdown_converter.src.pdf_extractor.pdfplumber.open')
    @patch('auto_doc_markdown_converter.src.pdf_extractor.fitz.open')
    def test_extract_simple_text_only(self, mock_fitz_open, mock_pdfplumber_open):
        """Test extracting text from a PDF with only text content."""
        # Mock pdfplumber
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.return_value = "This is simple text from page 1."
        mock_plumber_page.extract_tables.return_value = [] # No tables
        
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.pages = [mock_plumber_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_plumber_doc

        # Mock fitz (PyMuPDF)
        mock_pymupdf_page = MagicMock()
        mock_pymupdf_page.get_images.return_value = [] # No images
        
        mock_pymupdf_doc = MagicMock()
        mock_pymupdf_doc.load_page.return_value = mock_pymupdf_page
        mock_pymupdf_doc.__len__.return_value = 1 # Number of pages
        mock_fitz_open.return_value = mock_pymupdf_doc
        
        result = extract_content_from_pdf(self.mock_pdf_simple_text, self.test_results_dir)
        self.assertIsNotNone(result)
        text_content, extracted_data = result
        
        self.assertEqual(text_content.strip(), "This is simple text from page 1.")
        self.assertEqual(extracted_data, {})
        # Check if images subdir was created (it should be, even if no images)
        self.assertTrue(os.path.exists(os.path.join(self.test_results_dir, 'images')))


    @patch('auto_doc_markdown_converter.src.pdf_extractor.open', new_callable=mock_open) # Mock built-in open for saving images
    @patch('auto_doc_markdown_converter.src.pdf_extractor.pdfplumber.open')
    @patch('auto_doc_markdown_converter.src.pdf_extractor.fitz.open')
    def test_extract_content_with_image(self, mock_fitz_open, mock_pdfplumber_open, mock_file_open):
        """Test extracting content from a PDF with an image."""
        # Mock pdfplumber
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.return_value = "Text before image. Text after image."
        mock_plumber_page.extract_tables.return_value = []
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.pages = [mock_plumber_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_plumber_doc

        # Mock fitz (PyMuPDF)
        mock_pymupdf_page = MagicMock()
        # img_info format: (xref, smask_xref, width, height, bpc, colorspace_name, ..., name, ...)
        mock_pymupdf_page.get_images.return_value = [(123, 0, 100, 100, 8, "DeviceRGB", "img0")] 
        mock_pymupdf_doc = MagicMock()
        mock_pymupdf_doc.load_page.return_value = mock_pymupdf_page
        mock_pymupdf_doc.extract_image.return_value = {"image": b"fake_image_bytes", "ext": "png"}
        mock_pymupdf_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pymupdf_doc

        result = extract_content_from_pdf(self.mock_pdf_with_image, self.test_results_dir)
        self.assertIsNotNone(result)
        text_content, extracted_data = result

        expected_text_content = "Text before image. Text after image.\n\n[IMAGE_PLACEHOLDER:pdf_image_1.png]"
        self.assertEqual(text_content.strip(), expected_text_content.strip())
        self.assertIn("[IMAGE_PLACEHOLDER:pdf_image_1.png]", extracted_data)
        self.assertEqual(extracted_data["[IMAGE_PLACEHOLDER:pdf_image_1.png]"], "pdf_image_1.png")
        
        # Verify image file was "written"
        image_save_path = os.path.join(self.test_results_dir, 'images', 'pdf_image_1.png')
        mock_file_open.assert_called_with(image_save_path, 'wb')
        mock_file_open().write.assert_called_with(b"fake_image_bytes")

    @patch('auto_doc_markdown_converter.src.pdf_extractor.pdfplumber.open')
    @patch('auto_doc_markdown_converter.src.pdf_extractor.fitz.open')
    def test_extract_content_with_table(self, mock_fitz_open, mock_pdfplumber_open):
        """Test extracting content from a PDF with a table."""
        # Mock pdfplumber
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.return_value = "Text with a table."
        # Simulate a simple table: List[List[Optional[str]]]
        table_data = [["Header1", "Header2"], ["Cell1", "Cell2"], ["Cell3", None]]
        mock_plumber_page.extract_tables.return_value = [table_data]
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.pages = [mock_plumber_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_plumber_doc

        # Mock fitz (PyMuPDF) - no images for this test
        mock_pymupdf_page = MagicMock()
        mock_pymupdf_page.get_images.return_value = []
        mock_pymupdf_doc = MagicMock()
        mock_pymupdf_doc.load_page.return_value = mock_pymupdf_page
        mock_pymupdf_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pymupdf_doc

        result = extract_content_from_pdf(self.mock_pdf_with_table, self.test_results_dir)
        self.assertIsNotNone(result)
        text_content, extracted_data = result
        
        expected_text_content = "Text with a table.\n\n[TABLE_PLACEHOLDER_1]"
        self.assertEqual(text_content.strip(), expected_text_content.strip())
        self.assertIn("[TABLE_PLACEHOLDER_1]", extracted_data)
        
        expected_md_table = "| Header1 | Header2 |\n| --- | --- |\n| Cell1 | Cell2 |\n| Cell3 |  |"
        self.assertEqual(extracted_data["[TABLE_PLACEHOLDER_1]"], expected_md_table)

    @patch('auto_doc_markdown_converter.src.pdf_extractor.open', new_callable=mock_open)
    @patch('auto_doc_markdown_converter.src.pdf_extractor.pdfplumber.open')
    @patch('auto_doc_markdown_converter.src.pdf_extractor.fitz.open')
    def test_extract_content_with_image_and_table(self, mock_fitz_open, mock_pdfplumber_open, mock_file_open):
        """Test extracting content from a PDF with both an image and a table."""
        # Mock pdfplumber
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.return_value = "Page text with image and table."
        table_data = [["ColA", "ColB"], ["Data1", "Data2"]]
        mock_plumber_page.extract_tables.return_value = [table_data]
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.pages = [mock_plumber_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_plumber_doc

        # Mock fitz (PyMuPDF)
        mock_pymupdf_page = MagicMock()
        mock_pymupdf_page.get_images.return_value = [(456, 0, 50, 50, 8, "RGB", "img1")]
        mock_pymupdf_doc = MagicMock()
        mock_pymupdf_doc.load_page.return_value = mock_pymupdf_page
        mock_pymupdf_doc.extract_image.return_value = {"image": b"more_fake_bytes", "ext": "jpeg"}
        mock_pymupdf_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pymupdf_doc

        result = extract_content_from_pdf(self.mock_pdf_with_image_and_table, self.test_results_dir)
        self.assertIsNotNone(result)
        text_content, extracted_data = result

        # Order of placeholders depends on implementation (text -> images -> tables for now per page)
        expected_text_parts = [
            "Page text with image and table.",
            "[IMAGE_PLACEHOLDER:pdf_image_1.jpeg]",
            "[TABLE_PLACEHOLDER_1]"
        ]
        # Check if all parts are present and in rough order (flexible about exact newlines for now)
        # For more precise checking, you might want to split text_content and check parts.
        for part in expected_text_parts:
            self.assertIn(part, text_content)

        self.assertIn("[IMAGE_PLACEHOLDER:pdf_image_1.jpeg]", extracted_data)
        self.assertEqual(extracted_data["[IMAGE_PLACEHOLDER:pdf_image_1.jpeg]"], "pdf_image_1.jpeg")
        image_save_path = os.path.join(self.test_results_dir, 'images', 'pdf_image_1.jpeg')
        mock_file_open.assert_called_with(image_save_path, 'wb')
        mock_file_open().write.assert_called_with(b"more_fake_bytes")

        self.assertIn("[TABLE_PLACEHOLDER_1]", extracted_data)
        expected_md_table = "| ColA | ColB |\n| --- | --- |\n| Data1 | Data2 |"
        self.assertEqual(extracted_data["[TABLE_PLACEHOLDER_1]"], expected_md_table)

    @patch('auto_doc_markdown_converter.src.pdf_extractor.pdfplumber.open')
    @patch('auto_doc_markdown_converter.src.pdf_extractor.fitz.open')
    def test_extract_content_from_blank_pdf(self, mock_fitz_open, mock_pdfplumber_open):
        """Test with a PDF that has no text, images, or tables (or is empty)."""
        # Mock pdfplumber for an empty page
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.return_value = "" # No text
        mock_plumber_page.extract_tables.return_value = [] # No tables
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.pages = [mock_plumber_page] # One blank page
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_plumber_doc

        # Mock fitz (PyMuPDF) for a page with no images
        mock_pymupdf_page = MagicMock()
        mock_pymupdf_page.get_images.return_value = []
        mock_pymupdf_doc = MagicMock()
        mock_pymupdf_doc.load_page.return_value = mock_pymupdf_page
        mock_pymupdf_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_pymupdf_doc
        
        result = extract_content_from_pdf(self.mock_blank_pdf, self.test_results_dir)
        self.assertIsNotNone(result)
        text_content, extracted_data = result
        self.assertEqual(text_content, "") # Or just whitespace depending on how join works with empty parts
        self.assertEqual(extracted_data, {})

    @patch('auto_doc_markdown_converter.src.pdf_extractor.pdfplumber.open')
    @patch('auto_doc_markdown_converter.src.pdf_extractor.fitz.open')
    def test_extract_content_from_pdf_no_pages(self, mock_fitz_open, mock_pdfplumber_open):
        """Test with a PDF that pdfplumber says has no pages."""
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.pages = [] # No pages
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_plumber_doc

        # fitz mock not strictly necessary here as pdfplumber determines page loop
        mock_fitz_open.return_value = MagicMock() 

        result = extract_content_from_pdf(self.mock_blank_pdf, self.test_results_dir) # Path doesn't matter much due to mock
        self.assertIsNotNone(result)
        text_content, extracted_data = result
        self.assertEqual(text_content, "")
        self.assertEqual(extracted_data, {})


    def test_extract_content_from_corrupted_pdf(self):
        """
        Test extraction from a corrupted PDF file.
        This test uses an actual empty/corrupted file and expects graceful failure.
        """
        # pdfplumber.open or fitz.open should raise an error, and extract_content_from_pdf should catch it.
        # The real corrupted.pdf is a 0-byte file created earlier.
        if not os.path.exists(self.corrupted_pdf_path):
             # Create a dummy 0-byte file if it wasn't created by a previous step (e.g. if tests run out of order)
            with open(self.corrupted_pdf_path, 'w') as f:
                pass # Ensure it's a 0-byte file
            # self.fail(f"Corrupted PDF fixture not found at {self.corrupted_pdf_path}")


        result = extract_content_from_pdf(self.corrupted_pdf_path, self.test_results_dir)
        self.assertIsNone(result, "Expected None for a corrupted PDF that causes library errors.")

    @patch('auto_doc_markdown_converter.src.pdf_extractor.pdfplumber.open')
    @patch('auto_doc_markdown_converter.src.pdf_extractor.fitz.open')
    def test_fitz_library_unavailable_or_fails(self, mock_fitz_open, mock_pdfplumber_open):
        """Test scenario where fitz.open() raises an exception."""
        mock_fitz_open.side_effect = Exception("PyMuPDF general error")

        # Mock pdfplumber to still return some text
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.return_value = "Text content from pdfplumber."
        mock_plumber_page.extract_tables.return_value = []
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.pages = [mock_plumber_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_plumber_doc
        
        result = extract_content_from_pdf(self.mock_pdf_simple_text, self.test_results_dir)
        self.assertIsNotNone(result) # Function should still proceed with pdfplumber data
        text_content, extracted_data = result
        self.assertEqual(text_content.strip(), "Text content from pdfplumber.")
        self.assertEqual(extracted_data, {}, "No image data should be extracted if PyMuPDF fails.")


if __name__ == '__main__':
    # To run tests with more verbosity from command line: python -m unittest -v auto_doc_markdown_converter/tests/test_pdf_extractor.py
    unittest.main()