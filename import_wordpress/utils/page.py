from content.models import ContentPage

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

orphans = {
    "/dits-history/": "/about-us/dits-history/",
    "/how-we-are-structured/": "/about-us/how-we-are-structured/",
    "/lpg/": "/about-us/lpg/",
    "/our-management/": "/about-us/our-management/",
    "/our-ministers/": "/about-us/our-ministers/",
    "/our-unions/": "/about-us/our-unions/",
    "/our-vision-mission-and-values/": "/about-us/our-vision-mission-and-values/",
    "/single-departmental-plan/": "/about-us/single-departmental-plan/",
    "/asia-and-australasia-negotiations/": "guidance",
    "/book-clubs/": "guidance",
    "/change-management-in-dit/": "guidance",
    "/current-apprenticeships-and-funded-qualifications/": "guidance",
    "/di-guidance-and-support/": "guidance",
    "/dit/": "guidance",
    "/dit/2020-people-survey-corporate-functions-team-codes/": "guidance",
    "/dit/2020-people-survey-frequently-asked-questions-faqs/": "guidance",
    "/dit/2020-people-survey-global-strategy-directorate-team-codes/": "guidance",
    "/dit/2020-people-survey-global-trade-and-investment-team-codes/": "guidance",
    "/dit/2020-people-survey-global-trade-investment-overseas-team-codes/": "guidance",
    "/dit/2020-people-survey-great-team-code/": "guidance",
    "/dit/2020-people-survey-ministerial-strategy-directorate-team-codes/": "guidance",
    "/dit/2020-people-survey/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/communications-marketing/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/corporate-functions-commercial/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/global-strategy-directorate/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/great-peoplesurvey/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/gti-overseas-africa/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/gti-uk-regions/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/ministerial-strategy-directorate-peoplesurvey/": "guidance",
    "/dit/dit-people-survey-2019-headline-results/portfolio-development-directorate/": "guidance",
    "/dit/dit-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/chief-operating-officer-group-coo-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/communications-and-marketing-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/exports-group-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/great-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/international-strategy-directorate-isd-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/investment-group-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/ministerial-strategy-directorate-msd-people-survey-results-2018/": "guidance",
    "/dit/dit-people-survey-results-2018/trade-policy-group-tpg-people-survey-results-2018/": "guidance",
    "/dit/people-survey-results/": "guidance",
    "/dit/people-survey-results/communications/": "guidance",
    "/dit/people-survey-results/corporate-centre-people-survey/": "guidance",
    "/dit/people-survey-results/great/": "guidance",
    "/dit/people-survey-results/international-trade-and-investment-results/": "guidance",
    "/dit/people-survey-results/international-trade-and-investment-results/international-trade-and-investment-overseas-results/": "guidance",
    "/dit/people-survey-results/international-trade-and-investment-results/international-trade-and-investment-uk-results/": "guidance",
    "/dit/people-survey-results/ministerial-strategy-directorate/": "guidance",
    "/dit/people-survey-results/trade-policy-group-people-survey/": "guidance",
    "/dit/trade-policy-group-team-code-people-survey-2020/": "guidance",
    "/future-work-in-the-ddat-data-science-team/": "guidance",
    "/guidance-for-carers/": "guidance",
    "/how-data-science-teams-are-solving-complex-problems-across-dit/": "guidance",
    "/how-dit-data-science-solved-ukefs-struggle-to-identify-companies/": "guidance",
    "/identifying-the-public-procurement-landscape-by-matching-data-sets/": "guidance",
    "/introduction-to-procurement-in-dit/": "guidance",
    "/language-training-from-the-fco/": "guidance",
    "/managers-guide-to-mental-health/": "guidance",
    "/mapping-the-relationships-of-business-flows-between-the-uk-and-pakistan/": "guidance",
    "/mental-health-action-plan-mhap/": "guidance",
    "/natural-language-processing-to-identify-policy-feedback-on-eu-exit/": "guidance",
    "/negotiation-planning-and-capability/": "guidance",
    "/neurodiversity-celebration-week-16-to-22-march-2020/": "guidance",
    "/people-plan/": "guidance",
    "/people-plan/civil-service-covid-19-pulse-survey/": "guidance",
    "/people-plan/dit-people-survey-2019/": "guidance",
    "/people-plan/the-pulse-survey-2020/": "guidance",
    "/resilience/": "guidance",
    "/roles-and-responsibilities-recruit-interim-labour/": "guidance",
    "/sexual-harassment-survey-results/": "guidance",
    "/whistleblowing/": "guidance",
    "/redundancy-policy/": "policy",
}

# def check_for_orphan(path):
#     if orphans.has_key(path):
#         return




def get_page_type(path):
    for type_key, type_value in page_types.items():
        if path.startswith(type_key):
            return type_key

    print(f"ORPHAN PAGE: {path}")
    raise Exception("Orphan page")


def get_parent_path(path):
    parts = path.split("/")

    return f'{"/".join(parts[0:-2])}/'


def get_page_data(path, items):
    pages = items["page"]
    for key, value in pages.items():
        if value["link"] == path:
            return value

    raise Exception("Cannot find page")


def populate_page(path, items):
    #path = check_for_orphan(path)

    # Check for existence of page
    try:
        page_type_key = get_page_type(path)
    except:
        return None

    parent_path = get_parent_path(path)

    parent = ContentPage.objects.filter(
        legacy_path=parent_path,
    ).first()

    if not parent:
        parent = populate_page(parent_path, items)

    page_data = get_page_data(path, items)

    if page_type_key == path:
        return populate_section_homepage(
            page_data,
            page_types[page_type_key]["home_page_class"],
            items["attachment"],
            path,
        )

    page = ContentPage.objects.filter(
        legacy_path=path,
    ).first()

    if page:
        return page

    return create_page(
        page_data,
        page_types[page_type_key]["page_class"],
        parent,
        path,
        items["attachment"],
    )
