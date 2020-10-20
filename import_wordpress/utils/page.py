from about_us.models import (
    AboutUsHome,
    AboutUs,
)

from networks.models import (
    NetworksHome,
    Network,
)

from transition.models import TransitionHome, Transition

from tools.models import ToolsHome, Tool

from import_wordpress.parser.wagtail_content.page import (
    create_page,
    populate_homepage,
)


page_types = {
    "/about-us/": {
        "section_name": "about-us",
        "home_page_type": AboutUsHome,
        "page_type": AboutUs,
    },
    "/networks/": {
        "section_name": "networks",
        "home_page_type": NetworksHome,
        "page_type": Network,
    },
    "/transition-hub/": {
        "section_name": "transition-hub",
        "home_page_type": TransitionHome,
        "page_type": Transition,
    },
    "/tools/": {
        "section_name": "tools",
        "home_page_type": ToolsHome,
        "page_type": Tool,
    },
}


def set_page_content(page_key, page_value, items):
    for type_key, type_value in page_types.items():
        if page_value["link"].startswith(type_key):
            section_name = page_types[type_key]["section_name"]
            home_page_type = page_types[type_key]["home_page_type"]
            page_type = page_types[type_key]["page_type"]

            if page_value["link"] == type_key:
                populate_homepage(
                    items["page"][page_key],
                    home_page_type,
                    items["attachment"],
                    section_name,
                )
            else:
                # It's not the homepage
                link_parts = items["page"][page_key]["link"].split("/")
                link_parts.remove(section_name)
                link_parts = list(filter(lambda a: a != "", link_parts))

                parent = home_page_type.objects.filter(slug=section_name).first()

                for index, part in enumerate(link_parts, start=1):
                    if index == len(link_parts):

                        # print("page_key", page_key)
                        # print("page_value", page_value)
                        # print("items", items)

                        create_page(
                            items["page"][page_key],
                            page_type,
                            parent,
                            part,
                            items["attachment"],
                        )
                    else:
                        parent = page_type.objects.filter(slug=part).first()

                        if parent is None:
                            
                            print("PARENT IS NONE: slug=", part)
