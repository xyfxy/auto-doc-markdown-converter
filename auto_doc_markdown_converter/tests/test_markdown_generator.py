import unittest
from auto_doc_markdown_converter.src.markdown_generator import generate_markdown_from_labeled_text

class TestMarkdownGenerator(unittest.TestCase):

    def test_empty_input(self):
        self.assertEqual(generate_markdown_from_labeled_text(""), "")

    def test_whitespace_input(self):
        self.assertEqual(generate_markdown_from_labeled_text("   \n   "), "")

    def test_single_paragraph(self):
        labeled_text = "P: This is a simple paragraph."
        expected_markdown = "This is a simple paragraph."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_multiple_paragraphs(self):
        labeled_text = "P: First paragraph.\nP: Second paragraph."
        expected_markdown = "First paragraph.\n\nSecond paragraph."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_headings_h1_to_h6(self):
        labeled_text = (
            "H1: Main Title\n"
            "P: Intro paragraph.\n"
            "H2: Section 1\n"
            "H3: Subsection 1.1\n"
            "H4: Detail 1.1.1\n"
            "H5: Sub-detail 1.1.1.1\n"
            "H6: Fine Sub-detail 1.1.1.1.1\n"
            "P: Content under H6."
        )
        expected_markdown = (
            "# Main Title\n\n"
            "Intro paragraph.\n\n"
            "## Section 1\n\n"
            "### Subsection 1.1\n\n"
            "#### Detail 1.1.1\n\n"
            "##### Sub-detail 1.1.1.1\n\n"
            "###### Fine Sub-detail 1.1.1.1.1\n\n"
            "Content under H6."
        )
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_mixed_content_order(self):
        labeled_text = "P: Para 1\nH2: Title 2\nP: Para 2\nH1: Title 1"
        expected_markdown = "Para 1\n\n## Title 2\n\nPara 2\n\n# Title 1"
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_content_with_spaces_preserved(self):
        labeled_text = "P:  Spaced content  "
        expected_markdown = " Spaced content  " # Content's leading/trailing spaces are preserved
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_line_without_colon_is_skipped(self):
        # Corrected: Lines without colons are skipped by current markdown_generator.py
        labeled_text = "H1 Main Title Without Colon\nP: Valid paragraph."
        expected_markdown = "Valid paragraph."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_label_with_no_content(self):
        labeled_text = "H1: \nP: Paragraph after empty H1"
        expected_markdown = "# \n\nParagraph after empty H1" # Content is empty string
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_unknown_tag_is_skipped(self):
        # Corrected: Unknown tags are skipped by current markdown_generator.py
        labeled_text = "UNKNOWN: Some content\nP: Next paragraph"
        expected_markdown = "Next paragraph"
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)
        
    def test_case_sensitive_tags_lowercase_skipped(self):
        # Corrected: Tags are case-sensitive, lowercase 'h1:' would be skipped.
        labeled_text = "h1: lowercase title\nP: Real paragraph"
        expected_markdown = "Real paragraph"
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_input_with_only_empty_lines_after_strip(self):
        labeled_text = "\n   \n" # .strip() makes this empty
        expected_markdown = ""
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_valid_tags_with_leading_spaces_before_tag(self):
        labeled_text = "  H1: Title with leading space before tag\nP: Paragraph"
        expected_markdown = "# Title with leading space before tag\n\nParagraph"
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    # New tests for image placeholder processing
    def test_paragraph_with_single_image_placeholder(self):
        labeled_text = "P:[IMAGE_PLACEHOLDER:image1.png]"
        expected_markdown = "![](images/image1.png)"
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_paragraph_with_multiple_image_placeholders(self):
        labeled_text = "P:[IMAGE_PLACEHOLDER:img1.jpg] and [IMAGE_PLACEHOLDER:img2.gif]"
        expected_markdown = "![](images/img1.jpg) and ![](images/img2.gif)"
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_paragraph_with_text_and_image_placeholders(self):
        labeled_text = "P:Text before [IMAGE_PLACEHOLDER:pic.png] text after."
        expected_markdown = "Text before ![](images/pic.png) text after."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_paragraph_with_no_placeholders_remains_unchanged(self):
        labeled_text = "P:This is a normal paragraph."
        expected_markdown = "This is a normal paragraph."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

    def test_non_paragraph_lines_are_not_processed_for_images(self):
        labeled_text = "H1:[IMAGE_PLACEHOLDER:image.png]"
        # H1 content should be rendered as is, including the placeholder text, not as an image link.
        expected_markdown = "# [IMAGE_PLACEHOLDER:image.png]" 
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text), expected_markdown)

if __name__ == '__main__':
    unittest.main()
