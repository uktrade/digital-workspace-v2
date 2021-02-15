# from unittest.mock import Mock, patch
from django.test import (
    TestCase,
)

from import_wordpress.parser.block_content import parse_into_blocks


class ParseContent(TestCase):
    # @patch("import_wordpress.parser.block_content.create_image")
    # def test_parse_into_blocks(self, mock_image):
    #     image = Mock()
    #     image.pk = 1
    #
    #     mock_image.return_value = image
    #
    #     html = """Hello, I am text without a paragraph
    #         [caption id="x1" align="alignnone" width="512"]<img class="size-full wp-image-1" src="http://www.test.com/img-1.jpg" alt="Alt text 1" width="512" height="512" /> Caption 1[/caption]
    #         <strong>Strong used as heading</strong>
    #         <div class="img-in-child-1">
    #             <div class="img-in-child-2">
    #                 <p>Text with a paragraph 1</p>
    #                 <strong>Nested strong tag</strong>
    #                 [caption id="x2" align="alignnone" width="512"]<img class="size-full wp-image-2" src="http://www.test.com/img-2.jpg" alt="Alt text 2" width="512" height="512" /> Caption 2[/caption]
    #             </div>
    #         </div>
    #         <h2>Actual heading</h2>
    #         <p>Text with a paragraph 2</p>
    #         [caption id="x3" align="alignnone" width="512"]<img class="size-full wp-image-3" src="http://www.test.com/img-3.jpg" alt="Alt text 3" width="512" height="512" /> Caption 3[/caption]
    #         <p>Text with a paragraph 3</p>"""
    #
    #     attachments = {
    #         "1": {
    #             "attachment_url": "http://www.test.com/img-1.jpg",
    #             "title": "Test title 1",
    #         },
    #         "2": {
    #             "attachment_url": "http://www.test.com/img-2.jpg",
    #             "title": "Test title 2",
    #         },
    #         "3": {
    #             "attachment_url": "http://www.test.com/img-3.jpg",
    #             "title": "Test title 3",
    #         },
    #     }
    #
    #     blocks = parse_into_blocks(html, attachments)
    #
    #     # TODO - assert that blocks are correct - text, img, heading, text, img, heading, img, text

    def test_is_heading(self):
        html = """
            <strong>Strong used as heading</strong>
            <div class="img-in-child-1">
                <div class="img-in-child-2">
                    <p>Text with a paragraph 1</p>
                    <strong>Nested strong tag</strong>
                </div>
            </div>
            Paragraph of text without tag.

            Another paragraph of text without tag.

            Yet another paragraph of text without tag.
            <strong>Strong used as heading</strong>"""

        blocks = parse_into_blocks(html, [])

        # There should be 3 blocks - heading, text, heading
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0]["type"], "heading2")
        self.assertEqual(blocks[1]["type"], "text_section")
        self.assertEqual(blocks[2]["type"], "heading2")
