from django.template.defaultfilters import slugify

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
    populate_section_homepage,
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


def process_pages(pages):
    for key, value in pages:





def get_page_type(link):
    for type_key, type_value in page_types.items():
        if link.startswith(type_key):
            return type_key

    raise Exception(f"Cannot find page type for {link}")


def get_link_parts(link, section_name):
    link_parts = link.split("/")
    link_parts.remove(section_name)
    return list(filter(lambda a: a != "", link_parts))


def create_page_and_content(page_key, page, items):
    page_type = get_page_type(page["link"])
    section_name = page_types[page_type]["section_name"]
    home_page_type = page_types[page_type]["home_page_type"]

    # Check to see if it's a section homepage
    if page["link"] == page_type:
        populate_section_homepage(
            items["page"][page_key],
            home_page_type,
            items["attachment"],
            section_name,
        )
    else:
        create_child_page(page_key, page, items)


def get_page(page_link):
    for page in pages:
        if page["link"] == page_link:
            return page

def get_legacy_path(path):
    parts = path.split("/")
    return "/".join(parts[-1])

def populate_page(path):
    # Check if there is a parent
    parent_path = get_legacy_path(path)

    parent = ContentPage.objects.filter(
        legacy_path=parent_path,
    ).first()

    if not parent:
        parent = populate_page(parent_path)

    if parent.slug == "home":
        # populate_section_homepage(
        #     items["page"][page_key],
        #     home_page_type,
        #     items["attachment"],
        #     section_name,
        # )

        return section_homepage

    return create_page(
        items["page"][page_key],
        page_type,
        parent,
        part,
        items["attachment"],
    )






    for index, path_part in enumerate(path_parts):
        # if it's the first part, populate section home page
        if index == 0:
            # populate section home page
            # populate_section_homepage(
            #     items["page"][page_key],
            #     home_page_type,
            #     items["attachment"],
            #     section_name,
            # )
            # return section_home page
        else:
            # check to see if it has a parent


            section_home_page_type.objects.filter(legacy_path=).first()

                    if it does not have a parent
                        parent = populate_page(parent_path):
                            return create_page(
                                '',
                            )







def create_child_page(page_path):
    link_parts = get_link_parts(
        page["link"],
    )

    for index, part in enumerate(link_parts, start=1):
        parent_path = '/'.join(link_parts[1:index])
        parent_slug = slugify(parent_path)

        parent = Page.objects.filter(slug=parent_slug).first()

        if not parent:
            parent_page = get_page(parent_path)
            parent = create_child_page(parent_path)

        create_page(
            items["page"][page_key],
            page_type,
            parent,
            part,
            items["attachment"],
        )





def set_page_content(page_key, page_value, items):
    # Check to see if page exists

    for type_key, type_value in page_types.items():
        if page_value["link"].startswith(type_key):
            section_name = page_types[type_key]["section_name"]
            home_page_type = page_types[type_key]["home_page_type"]
            page_type = page_types[type_key]["page_type"]

            #  Check to see if this is a section home page
            if page_value["link"] == type_key:

                populate_section_homepage(
                    items["page"][page_key],
                    home_page_type,
                    items["attachment"],
                    section_name,
                )
            else:
                # It's not a section homepage
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

#
# def create_site_page():
#
#
