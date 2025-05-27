import unittest
import os
import sys
import tempfile
import shutil
import logging

# Add project root to sys.path to allow importing webapp.app
# This assumes that the script is run from a context where 'webapp' is a sibling to the project root's modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from webapp.app import app # Import the Flask app instance

# Disable most logging for cleaner test output
# Flask app's logger might behave differently; ensure it's also controlled if needed.
logging.disable(logging.CRITICAL) 

class TestAppPDFPreview(unittest.TestCase):
    """Test suite for the /preview_pdf/<filename> endpoint."""

    def setUp(self):
        """Set up test client and temporary upload folder."""
        app.config['TESTING'] = True
        app.config['DEBUG'] = False # Ensure debug mode is off for predictable error handling
        self.client = app.test_client()

        # Create a temporary directory for UPLOAD_FOLDER
        self.temp_upload_dir = tempfile.mkdtemp()
        app.config['UPLOAD_FOLDER'] = self.temp_upload_dir
        
        self.test_pdf_filename = "test_preview.pdf"
        self.test_txt_filename = "dummy_file.txt"
        self.dummy_pdf_content = b"This is dummy PDF content."

        # Create a dummy PDF file in the temporary upload folder
        with open(os.path.join(self.temp_upload_dir, self.test_pdf_filename), 'wb') as f:
            f.write(self.dummy_pdf_content)

        # Create a dummy TXT file
        with open(os.path.join(self.temp_upload_dir, self.test_txt_filename), 'w') as f:
            f.write("This is a text file.")

    def tearDown(self):
        """Remove the temporary upload folder after tests."""
        shutil.rmtree(self.temp_upload_dir)

    def test_preview_pdf_success(self):
        """Test successful retrieval of a PDF file for preview."""
        response = self.client.get(f'/preview_pdf/{self.test_pdf_filename}')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/pdf')
        self.assertEqual(response.data, self.dummy_pdf_content)

    def test_preview_pdf_file_not_found(self):
        """Test response when the requested PDF file is not found."""
        response = self.client.get('/preview_pdf/non_existent_file.pdf')
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json') # Assuming error is JSON
        json_data = response.get_json()
        self.assertIn('error', json_data)
        self.assertEqual(json_data['error'], '原始 PDF 文件未找到。') # Match error message in app.py

    def test_preview_pdf_not_a_pdf_extension(self):
        """Test response when the requested file does not have a .pdf extension."""
        response = self.client.get(f'/preview_pdf/{self.test_txt_filename}')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, 'application/json')
        json_data = response.get_json()
        self.assertIn('error', json_data)
        self.assertEqual(json_data['error'], '请求的文件不是 PDF 格式。') # Match error message in app.py

    def test_preview_pdf_path_traversal_attempt(self):
        """Test a path traversal attempt (though send_from_directory should handle this)."""
        # This tests the robustness of send_from_directory and Werkzeug's path handling.
        # It's unlikely to succeed in traversal but good to have a check.
        response = self.client.get('/preview_pdf/../../../../etc/passwd')
        self.assertEqual(response.status_code, 404) # Expecting not found, not a 400 from our ext check

if __name__ == '__main__':
    unittest.main()
