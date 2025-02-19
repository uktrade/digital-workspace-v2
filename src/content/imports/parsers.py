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

    def paragraph_to_heading(self, paragraph: Paragraph, heading_level):
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
        """
        text_list = []
        for content in paragraph.iter_inner_content():
            text = content.text
            if isinstance(content, Run):
                if content.bold:
                    text = self.generate_simple_tag(text, "b")
                if content.italic:
                    text = self.generate_simple_tag(text, "em")
                text_list.append(text)
            elif isinstance(content, Hyperlink):
                text_list.append(self.generate_a_tag(text, content.address))

        content = mark_safe("".join(text_list))
        return {"type": "html", "value": self.generate_simple_tag(content, outer_tag)}

    def parse(self):
        """
        Parse the document and return a set of intermediate {'type': type, 'value': value} blocks that represent it.
        """

        title = self.document.core_properties.title

        paragraphs: list[Paragraph] = self.document.paragraphs

        blocks = []
        for paragraph in paragraphs:
            p_style_name = paragraph.style.name
            if p_style_name not in KNOWN_NAMES:
                raise Exception(f"Unknown paragraph style: {p_style_name}")

            if p_style_name.startswith("Heading "):
                heading_level = p_style_name[8:9]
                if heading_level == "1" and not title:
                    title = paragraph.text.strip()

                if heading_block := self.paragraph_to_heading(paragraph, heading_level):
                    blocks.append(heading_block)
            else:
                converted_block = self.paragraph_to_html(paragraph)
                if block_val := converted_block["value"]:
                    blocks.append(
                        {
                            "type": "html",
                            "value": block_val,
                        }
                    )

        return {"title": title, "elements": blocks}
