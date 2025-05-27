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
        # H1 content should be rendered as is, including the placeholder text, not as an image link,
        # if using the old direct replacement. With extracted_data, it depends on how it's applied.
        # The current generate_markdown_from_labeled_text applies replacements globally *after* block construction.
        # So, this test's expectation will change if the placeholder is in extracted_data.
        # If [IMAGE_PLACEHOLDER:image.png] is NOT in extracted_data, it will be handled by fallback.
        # If it IS in extracted_data, it WILL be replaced.
        
        # Scenario 1: Placeholder NOT in extracted_data (tests fallback)
        expected_markdown_fallback = "# ![](images/image.png)" # Fallback regex IMAGE_PLACEHOLDER_RE will catch it
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text, None), expected_markdown_fallback)

        # Scenario 2: Placeholder IS in extracted_data
        extracted_data_for_h1 = {"[IMAGE_PLACEHOLDER:image.png]": "image.png"}
        expected_markdown_with_data = "# ![](images/image.png)"
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text, extracted_data_for_h1), expected_markdown_with_data)


    def test_generate_markdown_with_extracted_data_for_images_and_tables(self):
        """
        Tests replacement of image and table placeholders using the extracted_data dictionary.
        """
        labeled_text = (
            "P:Text with an image [IMAGE_PLACEHOLDER:map.png] here.\n"
            "P:And a table [TABLE_PLACEHOLDER_1] follows.\n"
            "H2:Another section with [IMAGE_PLACEHOLDER:chart.jpeg]"
        )
        extracted_data = {
            "[IMAGE_PLACEHOLDER:map.png]": "map.png",  # Value is filename
            "[TABLE_PLACEHOLDER_1]": "|ID|Value|\n|--|-----|\n|1 |Alpha|\n|2 |Beta |", # Value is Markdown table
            "[IMAGE_PLACEHOLDER:chart.jpeg]": "chart.jpeg"
        }
        
        # Expected: Placeholders in P and H2 should be replaced.
        expected_markdown = (
            "Text with an image ![](images/map.png) here.\n\n"
            "And a table |ID|Value|\n|--|-----|\n|1 |Alpha|\n|2 |Beta | follows.\n\n"
            "## Another section with ![](images/chart.jpeg)"
        )
        
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text, extracted_data), expected_markdown)

    def test_placeholder_not_in_extracted_data(self):
        """
        Tests behavior when a placeholder is in text but not in extracted_data.
        It should use the fallback regex replacement for images, and keep table placeholders.
        """
        labeled_text = "P:Image [IMAGE_PLACEHOLDER:missing_img.png] and table [TABLE_PLACEHOLDER_99]."
        extracted_data = {
            "[IMAGE_PLACEHOLDER:other_img.png]": "other_img.png" 
            # missing_img.png and TABLE_PLACEHOLDER_99 are not in here
        }
        # Fallback for IMAGE_PLACEHOLDER_RE will convert image. Table placeholder remains.
        expected_markdown = "Image ![](images/missing_img.png) and table [TABLE_PLACEHOLDER_99]."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text, extracted_data), expected_markdown)

    def test_empty_extracted_data_or_none(self):
        labeled_text = "P:Image [IMAGE_PLACEHOLDER:img.png] and table [TABLE_PLACEHOLDER_1]."
        # Fallback for IMAGE_PLACEHOLDER_RE will convert image. Table placeholder remains.
        expected_markdown_none_data = "Image ![](images/img.png) and table [TABLE_PLACEHOLDER_1]."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text, None), expected_markdown_none_data)
        
        expected_markdown_empty_data = "Image ![](images/img.png) and table [TABLE_PLACEHOLDER_1]."
        self.assertEqual(generate_markdown_from_labeled_text(labeled_text, {}), expected_markdown_empty_data)


if __name__ == '__main__':
    unittest.main()
