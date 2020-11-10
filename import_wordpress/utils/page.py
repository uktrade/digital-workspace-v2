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
    "/asia-and-australasia-negotiations/": "/working-at-dit/policies-and-guidance/guidance/asia-and-australasia-negotiations/",
    "/book-clubs/": "/working-at-dit/policies-and-guidance/guidance/book-clubs/",
    "/change-management-in-dit/": "/working-at-dit/policies-and-guidance/guidance/change-management-in-dit/",
    "/current-apprenticeships-and-funded-qualifications/": "/working-at-dit/policies-and-guidance/guidance/current-apprenticeships-and-funded-qualifications/",
    "/di-guidance-and-support/": "/working-at-dit/policies-and-guidance/guidance/di-guidance-and-support/",
    "/dit/": "/working-at-dit/policies-and-guidance/guidance/dit/",
    "/dit/2020-people-survey-corporate-functions-team-codes/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey-corporate-functions-team-codes/",
    "/dit/2020-people-survey-frequently-asked-questions-faqs/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey-frequently-asked-questions-faqs/",
    "/dit/2020-people-survey-global-strategy-directorate-team-codes/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey-global-strategy-directorate-team-codes/",
    "/dit/2020-people-survey-global-trade-and-investment-team-codes/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey-global-trade-and-investment-team-codes/",
    "/dit/2020-people-survey-global-trade-investment-overseas-team-codes/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey-global-trade-investment-overseas-team-codes/",
    "/dit/2020-people-survey-great-team-code/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey-great-team-code/",
    "/dit/2020-people-survey-ministerial-strategy-directorate-team-codes/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey-ministerial-strategy-directorate-team-codes/",
    "/dit/2020-people-survey/": "/working-at-dit/policies-and-guidance/guidance/dit/2020-people-survey/",
    "/dit/dit-people-survey-2019-headline-results/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/",
    "/dit/dit-people-survey-2019-headline-results/communications-marketing/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/communications-marketing/",
    "/dit/dit-people-survey-2019-headline-results/corporate-functions-commercial/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/corporate-functions-commercial/",
    "/dit/dit-people-survey-2019-headline-results/global-strategy-directorate/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/global-strategy-directorate/",
    "/dit/dit-people-survey-2019-headline-results/great-peoplesurvey/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/great-peoplesurvey/",
    "/dit/dit-people-survey-2019-headline-results/gti-overseas-africa/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/gti-overseas-africa/",
    "/dit/dit-people-survey-2019-headline-results/gti-uk-regions/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/gti-uk-regions/",
    "/dit/dit-people-survey-2019-headline-results/ministerial-strategy-directorate-peoplesurvey/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/ministerial-strategy-directorate-peoplesurvey/",
    "/dit/dit-people-survey-2019-headline-results/portfolio-development-directorate/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-2019-headline-results/portfolio-development-directorate/",
    "/dit/dit-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/chief-operating-officer-group-coo-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/chief-operating-officer-group-coo-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/communications-and-marketing-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/communications-and-marketing-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/exports-group-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/exports-group-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/great-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/great-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/international-strategy-directorate-isd-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/international-strategy-directorate-isd-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/investment-group-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/investment-group-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/ministerial-strategy-directorate-msd-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/ministerial-strategy-directorate-msd-people-survey-results-2018/",
    "/dit/dit-people-survey-results-2018/trade-policy-group-tpg-people-survey-results-2018/": "/working-at-dit/policies-and-guidance/guidance/dit/dit-people-survey-results-2018/trade-policy-group-tpg-people-survey-results-2018/",
    "/dit/people-survey-results/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/",
    "/dit/people-survey-results/communications/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/communications/",
    "/dit/people-survey-results/corporate-centre-people-survey/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/corporate-centre-people-survey/",
    "/dit/people-survey-results/great/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/great/",
    "/dit/people-survey-results/international-trade-and-investment-results/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/international-trade-and-investment-results/",
    "/dit/people-survey-results/international-trade-and-investment-results/international-trade-and-investment-overseas-results/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/international-trade-and-investment-results/international-trade-and-investment-overseas-results/",
    "/dit/people-survey-results/international-trade-and-investment-results/international-trade-and-investment-uk-results/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/international-trade-and-investment-results/international-trade-and-investment-uk-results/",
    "/dit/people-survey-results/ministerial-strategy-directorate/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/ministerial-strategy-directorate/",
    "/dit/people-survey-results/trade-policy-group-people-survey/": "/working-at-dit/policies-and-guidance/guidance/dit/people-survey-results/trade-policy-group-people-survey/",
    "/dit/trade-policy-group-team-code-people-survey-2020/": "/working-at-dit/policies-and-guidance/guidance/dit/trade-policy-group-team-code-people-survey-2020/",
    "/future-work-in-the-ddat-data-science-team/": "/working-at-dit/policies-and-guidance/guidance/future-work-in-the-ddat-data-science-team/",
    "/guidance-for-carers/": "/working-at-dit/policies-and-guidance/guidance/guidance-for-carers/",
    "/how-data-science-teams-are-solving-complex-problems-across-dit/": "/working-at-dit/policies-and-guidance/guidance/how-data-science-teams-are-solving-complex-problems-across-dit/",
    "/how-dit-data-science-solved-ukefs-struggle-to-identify-companies/": "/working-at-dit/policies-and-guidance/guidance/how-dit-data-science-solved-ukefs-struggle-to-identify-companies/",
    "/identifying-the-public-procurement-landscape-by-matching-data-sets/": "/working-at-dit/policies-and-guidance/guidance/identifying-the-public-procurement-landscape-by-matching-data-sets/",
    "/introduction-to-procurement-in-dit/": "/working-at-dit/policies-and-guidance/guidance/introduction-to-procurement-in-dit/",
    "/language-training-from-the-fco/": "/working-at-dit/policies-and-guidance/guidance/language-training-from-the-fco/",
    "/managers-guide-to-mental-health/": "/working-at-dit/policies-and-guidance/guidance/managers-guide-to-mental-health/",
    "/mapping-the-relationships-of-business-flows-between-the-uk-and-pakistan/": "/working-at-dit/policies-and-guidance/guidance/mapping-the-relationships-of-business-flows-between-the-uk-and-pakistan/",
    "/mental-health-action-plan-mhap/": "/working-at-dit/policies-and-guidance/guidance/mental-health-action-plan-mhap/",
    "/natural-language-processing-to-identify-policy-feedback-on-eu-exit/": "/working-at-dit/policies-and-guidance/guidance/natural-language-processing-to-identify-policy-feedback-on-eu-exit/",
    "/negotiation-planning-and-capability/": "/working-at-dit/policies-and-guidance/guidance/negotiation-planning-and-capability/",
    "/neurodiversity-celebration-week-16-to-22-march-2020/": "/working-at-dit/policies-and-guidance/guidance/neurodiversity-celebration-week-16-to-22-march-2020/",
    "/people-plan/": "/working-at-dit/policies-and-guidance/guidance/people-plan/",
    "/people-plan/civil-service-covid-19-pulse-survey/": "/working-at-dit/policies-and-guidance/guidance/people-plan/civil-service-covid-19-pulse-survey/",
    "/people-plan/dit-people-survey-2019/": "/working-at-dit/policies-and-guidance/guidance/people-plan/dit-people-survey-2019/",
    "/people-plan/the-pulse-survey-2020/": "/working-at-dit/policies-and-guidance/guidance/people-plan/the-pulse-survey-2020/",
    "/resilience/": "/working-at-dit/policies-and-guidance/guidance/resilience/",
    "/roles-and-responsibilities-recruit-interim-labour/": "/working-at-dit/policies-and-guidance/guidance/roles-and-responsibilities-recruit-interim-labour/",
    "/sexual-harassment-survey-results/": "/working-at-dit/policies-and-guidance/guidance/sexual-harassment-survey-results/",
    "/whistleblowing/": "/working-at-dit/policies-and-guidance/guidance/whistleblowing/",
    "/redundancy-policy/": "/working-at-dit/policies-and-guidance/policy/redundancy-policy/",
}


def check_for_orphan(path):
    if path in orphans:
        return orphans[path]

    return None


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
    orphan_path = check_for_orphan(path)

    if orphan_path:
        path = orphan_path

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
