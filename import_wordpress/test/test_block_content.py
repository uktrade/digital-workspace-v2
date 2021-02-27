from django.test import (
    TestCase,
)

from import_wordpress.parser.block_content import parse_into_blocks
from import_wordpress.test.factories import WagtailImageFactory
from user.test.factories import UserFactory


class TestBlockContent(TestCase):
    def test_image_process(self):
        user = UserFactory()

        # Create image records - these will exist after
        # the S3 import process is run
        for i in range(3):
            WagtailImageFactory(
                file=f"test/img-{i+1}.jpg",
                uploaded_by_user_id=user.id,
            )

        html = """Hello, I am text without a paragraph
            [caption id="x1" align="alignnone" width="512"]<img class="size-full wp-image-1" src="http://www.test.com/img-1.jpg" alt="Alt text 1" width="512" height="512" /> Caption 1[/caption]
            Some text without a paragraph
            <p></p>
             
            
            <div class="img-in-child-1">
                <div class="img-in-child-2">
                    <p>Text with a paragraph 1</p>
                    <strong>Nested strong tag</strong>
                    [caption id="x2" align="alignnone" width="512"]<img class="size-full wp-image-2" src="http://www.test.com/img-2.jpg" alt="Alt text 2" width="512" height="512" /> Caption 2[/caption]
                </div>
            </div>
            <p>Text with a paragraph</p>
            [caption id="x3" align="alignnone" width="512"]<img class="size-full wp-image-3" src="http://www.test.com/img-3.jpg" alt="Alt text 3" width="512" height="512" /> Caption 3[/caption]
            <p>Text with a paragraph</p>"""

        attachments = {
            "1": {
                "attachment_url": "http://www.test.com/test/img-1.jpg",
                "title": "Test title 1",
            },
            "2": {
                "attachment_url": "http://www.test.com/test/img-2.jpg",
                "title": "Test title 2",
            },
            "3": {
                "attachment_url": "http://www.test.com/test/img-3.jpg",
                "title": "Test title 3",
            },
        }

        blocks = parse_into_blocks(html, attachments)

        self.assertEqual(len(blocks), 7)
        self.assertEqual(blocks[0]["type"], "text_section")
        self.assertEqual(blocks[1]["type"], "image")
        self.assertEqual(blocks[2]["type"], "text_section")
        self.assertEqual(blocks[3]["type"], "image")
        self.assertEqual(blocks[4]["type"], "text_section")
        self.assertEqual(blocks[5]["type"], "image")
        self.assertEqual(blocks[6]["type"], "text_section")

    def test_is_heading(self):
        html = """
            <strong>Strong used as heading</strong>
            <div class="test">
                <div class="inner-test">
                    <p>Text with a paragraph 1</p>
                    <strong>Nested strong tag</strong>
                </div>
            </div>
            Paragraph of text without tag.
            <h2>Actual heading</h2>
            Another paragraph of text without tag.
            Yet another paragraph of text without tag.
            <strong>Strong used as heading</strong>"""

        blocks = parse_into_blocks(html, [])

        # There should be 3 blocks - heading, text, heading
        self.assertEqual(len(blocks), 5)
        self.assertEqual(blocks[0]["type"], "heading2")
        self.assertEqual(blocks[0]["value"], "Strong used as heading")

        self.assertEqual(blocks[1]["type"], "text_section")
        self.assertEqual(
            blocks[1]["value"],
            (
                "<p>Text with a paragraph 1</p>"
                "<p><strong>Nested strong tag</strong></p>"
                "<p>Paragraph of text without tag.</p>"
            ),
        )

        self.assertEqual(blocks[2]["type"], "heading2")

        self.assertEqual(blocks[3]["type"], "text_section")
        self.assertEqual(
            blocks[3]["value"],
            "<p>Another paragraph of text without tag.</p><p>Yet another paragraph of text without tag.</p>",
        )

        self.assertEqual(blocks[4]["type"], "heading2")

    def test_links_have_spaces_before_and_after(self):
        html = 'this is some text <a href="#">test</a> <strong>some</strong> other text'

        blocks = parse_into_blocks(html, [])

        self.assertEqual(blocks[0]["type"], "text_section")
        self.assertEqual(
            blocks[0]["value"],
            (
                '<p>this is some text <a href="#">test</a> <strong>some</strong> other text</p>'
            ),
        )
