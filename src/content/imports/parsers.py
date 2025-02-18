from wagtail_content_import.parsers.microsoft import DocxParser


class DocxParser(DocxParser):
    def parse(self):
        """
        Parse the document and return a set of intermediate {'type': type, 'value': value} blocks that represent it.
        """
        blocks = []

        title = self.document.core_properties.title

        html_content = ""

        for paragraph in self.document.paragraphs:
            # TODO: plan support for a variety of types
            print(paragraph.style.name)
            print(paragraph.text)
            if paragraph.style.name[:-1] == "Heading ":
                if html_content:
                    blocks.append(
                        {
                            "type": "html",
                            "value": html_content,
                        }
                    )
                    html_content = ""

                heading_level = paragraph.style.name[-1]
                if not title and heading_level == "1":
                    title = paragraph.text

                blocks.append(
                    {
                        "type": f"heading{heading_level}",
                        "value": paragraph.text.strip(),
                    }
                )
            else:
                converted_block = self.paragraph_to_html(paragraph)
                html_content += converted_block["value"]

        return {"title": title, "elements": blocks}
