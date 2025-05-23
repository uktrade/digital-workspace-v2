from datetime import timedelta

from django.db.models import Q, QuerySet
from django.utils.timezone import now

from about_us.models import AboutUsHome
from content.models import BasePage, BlogIndex, NavigationPage
from country_fact_sheet.models import CountryFactSheetHome
from events.models import EventsHome
from home.models import HomePage
from networks.models import NetworksHome
from news.models import NewsHome
from peoplefinder.models import Person
from tools.models import Tool, ToolsHome
from working_at_dit.models import (
    GuidanceHome,
    HowDoIHome,
    PoliciesAndGuidanceHome,
    PoliciesHome,
    Topic,
    TopicHome,
    WorkingAtDITHome,
)


# This list will need to be discussed with the wider team
PAGES_TO_EXCLUDE = [
    AboutUsHome,
    BlogIndex,
    CountryFactSheetHome,
    EventsHome,
    GuidanceHome,
    HomePage,
    HowDoIHome,
    NavigationPage,
    NetworksHome,
    NewsHome,
    PoliciesAndGuidanceHome,
    PoliciesHome,
    Tool,
    ToolsHome,
    Topic,
    TopicHome,
    WorkingAtDITHome,
]


CUTOFF = now() - timedelta(days=365)


# ask if this function is fine or if we want to pass a cutoff date a parameter to make it more flexible
# eg cutoff_date=None -> if cutoff_date is None: cutoff_date = now() - timedelta(days=365)
def get_pages_to_update() -> QuerySet[BasePage]:
    return BasePage.objects.not_exact_type(*PAGES_TO_EXCLUDE).filter(
        Q(confirmed_needed_at__lte=CUTOFF) | Q(confirmed_needed_at__isnull=True),
        last_published_at__lte=CUTOFF,
    )


def update_confirm_needed_at(page: BasePage) -> None:
    page.confirmed_needed_at = now()
    page.save(update_fields=["confirmed_needed_at"])


def get_pages_to_archive() -> QuerySet[BasePage]:
    return BasePage.objects.not_exact_type(*PAGES_TO_EXCLUDE).filter(
        Q(confirmed_needed_at_isnull=True) | Q(confirmed_needed_at__lte=CUTOFF),
        archive_notification_sent_at__lte=now() - timedelta(days=30),
        last_published_at__lte=CUTOFF,
    )


def get_people_to_contact(page: BasePage) -> list[Person]:
    """
    Returns a unique list of people related to page in order of importance.
    """
    people = []
    if content_owner := getattr(page, "content_owner", None):
        content_owner not in people and people.append(content_owner)

    if page.page_author:
        page.page_author not in people and people.append(page.page_author)

    if page.get_latest_publisher():
        page.get_latest_publisher().profile not in people and people.append(
            page.get_latest_publisher().profile
        )

    if page.owner:
        page.owner not in people and people.append(page.owner.profile)

    return people
