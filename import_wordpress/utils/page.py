import logging

from about_us.models import (
    AboutUs,
    AboutUsHome,
)
from content.models import ContentPage
from import_wordpress.parser.wagtail_content.page import (
    SectionHomepage,
    StandardPage,
)
from networks.models import (
    Network,
    NetworksHome,
)
from tools.models import Tool, ToolsHome
from transition.models import Transition, TransitionHome


logger = logging.getLogger(__name__)


page_types = {
    "/about-us/": {
        "section_name": "about-us",
        "home_page_class": AboutUsHome,
        "page_class": AboutUs,
    },
    "/networks/": {
        "section_name": "networks",
        "home_page_class": NetworksHome,
        "page_class": Network,
    },
    "/transition-hub/": {
        "section_name": "transition-hub",
        "home_page_class": TransitionHome,
        "page_class": Transition,
    },
    "/tools/": {
        "section_name": "tools",
        "home_page_class": ToolsHome,
        "page_class": Tool,
    },
}


def get_page_type(path):
    for type_key, _type_value in page_types.items():
        if path.startswith(type_key):
            return type_key

    logger.error(f"ORPHAN PAGE: {path}")
    raise Exception("Orphan page")


def get_parent_path(path):
    parts = path.split("/")

    return f'{"/".join(parts[0:-2])}/'


def get_page_data(path, items):
    pages = items["page"]
    for _key, value in pages.items():
        if value["link"] == path:
            return value

    logger.error("Unable to find path: ", path)
    raise Exception("Cannot find page")


def populate_page(path, items):
    # Check for existence of page
    try:
        page_type_key = get_page_type(path)
    except Exception:
        return None

    parent_path = get_parent_path(path)

    parent = ContentPage.objects.filter(
        legacy_path=parent_path,
    ).first()

    if not parent:
        parent = populate_page(parent_path, items)

    page_data = get_page_data(path, items)

    if page_type_key == path:
        return SectionHomepage(
            page_content=page_data,
            content_class=page_types[page_type_key]["home_page_class"],
            attachments=items["attachment"],
            path=path,
        ).create()

    page = ContentPage.objects.filter(
        legacy_path=path,
    ).first()

    if page:
        return page

    standard_page = StandardPage(
        page_content=page_data,
        content_class=page_types[page_type_key]["page_class"],
        parent=parent,
        path=path,
        attachments=items["attachment"],
    )
    if standard_page.live:
        return standard_page.create()

    return None
