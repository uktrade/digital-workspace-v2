from django.utils.html import format_html
from django.utils.safestring import mark_safe
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from wagtail_content_import.parsers.microsoft import DocxParser


HEADING_PARAGRAPH_NAMES = [
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Heading 5",
    "Heading 1_DBT",
    "Heading 2_DBT",
    "Heading 3_DBT",
    "Heading 4_DBT",
    "Heading 5_DBT",
]

OTHER_NAMES = [
    "Normal",
    "DBT num list",
    "Bullet List 1",
]

KNOWN_NAMES = HEADING_PARAGRAPH_NAMES + OTHER_NAMES


class DocxParser(DocxParser):
    def generate_a_tag(self, content, href):
        return (
            format_html('<a href="{href}">{content}</a>', href=href, content=content)
            if content
            else ""
        )

    def paragraph_to_heading(
        self, paragraph: Paragraph, heading_level
    ) -> None | dict[str, str]:
        if not paragraph.text:
            return None

        block_val = paragraph.text.strip()
        if not block_val:
            return None

        return {
            "type": f"heading{heading_level}",
            "value": block_val,
        }

    def paragraph_to_html(self, paragraph: Paragraph, outer_tag="p"):
        """
        Compile a paragraph into a HTML string, optionally with semantic markup for styles.
        Returns a dictionary of the form:
        {
            'type': 'html',
            'value': html
        }
        OR
        {
            'type': 'html-list',
            'list_type': 'ol' | 'ul',
            'value': html
        }
        """
        text_list = []
        for content in paragraph.iter_inner_content():
            text = content.text
            match content:
                case Run():
                    if content.bold:
                        text = self.generate_simple_tag(text, "b")
                    if content.italic:
                        text = self.generate_simple_tag(text, "em")
                    text_list.append(text)
                case Hyperlink():
                    text_list.append(self.generate_a_tag(text, content.address))

        content = mark_safe("".join(text_list))  # noqa: S308

        block = {
            "type": "html",
            "value": "",
        }

        if paragraph.style.name in ["DBT num list", "Bullet List 1"]:
            block["type"] = "html-list"
            block["list_type"] = "ul"
            block["value"] = self.generate_simple_tag(content, "li")

            if paragraph.style.name == "DBT num list":
                block["list_type"] = "ol"

            return block

        block["value"] = self.generate_simple_tag(content, outer_tag)
        return block

    def get_block_type_for_paragraph(self, paragraph: Paragraph) -> tuple[str, dict]:
        if paragraph.style.name.startswith("Heading "):
            return "heading", {
                "heading_level": paragraph.style.name[8:9],
            }
        return "html", {}

    def parse(self):
        """
        Parse the document and return a set of intermediate {'type': type, 'value': value} blocks that represent it.
        """

        title = self.document.core_properties.title

        blocks = []

        paragraphs: list[Paragraph] = self.document.paragraphs
        for paragraph in paragraphs:
            p_style_name = paragraph.style.name
            if p_style_name not in KNOWN_NAMES:
                raise Exception(f"Unknown paragraph style: {p_style_name}")

            block_type, block_data = self.get_block_type_for_paragraph(paragraph)
            if block_type == "heading":
                heading_level = block_data["heading_level"]

                if heading_level == "1" and not title:
                    title = paragraph.text.strip()

                if heading_block := self.paragraph_to_heading(paragraph, heading_level):
                    blocks.append(heading_block)

            else:
                converted_block = self.paragraph_to_html(paragraph)

                if block_val := converted_block["value"]:
                    # if blocks and blocks[-1]["type"] == "html":
                    #     blocks[-1]["value"] += block_val
                    # else:
                    blocks.append(converted_block)

        # SECOND PASS

        final_blocks = []
        html_content = ""

        for i, block in enumerate(blocks):
            prev_block = blocks[i - 1] if i > 0 else None
            next_block = blocks[i + 1] if i < len(blocks) - 1 else None

            if block["type"] == "html-list":
                if prev_block and (
                    prev_block["type"] != "html-list"
                    or block["list_type"] != prev_block["list_type"]
                ):
                    # Open the list
                    html_content += f"<{block['list_type']}>"

                # Add the list item
                html_content += block["value"]

                if next_block and (
                    next_block["type"] != "html-list"
                    or block["list_type"] != next_block["list_type"]
                ):
                    # Close the list
                    html_content += f"</{block['list_type']}>"

                    if next_block["type"] != "html-list":
                        final_blocks.append(
                            {
                                "type": "html",
                                "value": html_content,
                            }
                        )
                        html_content = ""
            else:
                final_blocks.append(block)

        return {"title": title, "elements": final_blocks}
