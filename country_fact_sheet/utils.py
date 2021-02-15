from defusedxml import ElementTree

WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PARA = WORD_NAMESPACE + "p"
TEXT = WORD_NAMESPACE + "t"
STYLE_CONTAINER = WORD_NAMESPACE + "pPr"
STYLE = WORD_NAMESPACE + "pStyle"

HEADERS = [
    "Heading1",
    "Heading2",
    "Heading6",
]


def get_style(paragraph):
    style_value = None

    styling_containers = paragraph.findall(STYLE_CONTAINER)

    if len(styling_containers) == 1:
        style = styling_containers[0].findall(STYLE)

        if len(style) == 1:
            style_value = style[0].get(WORD_NAMESPACE + "val")
        elif len(style) > 1:
            raise Exception("Found more than one style tag")

    elif len(styling_containers) > 1:
        raise Exception("Found more than one style container tag")

    return style_value


def process_factsheet(xml_file):
    tree = ElementTree.parse(xml_file).getroot()
    output_root = ElementTree.Element("div")

    for paragraph in tree.iter(PARA):
        style = get_style(paragraph)

        if style in HEADERS:
            output_current = ElementTree.SubElement(output_root, "h3")
        else:
            output_current = ElementTree.SubElement(output_root, "p")

        texts = [node.text for node in paragraph.iter(TEXT) if node.text]

        para_text = ""

        for text in texts:
            para_text = para_text + text

        output_current.text = para_text
