from datetime import datetime, timedelta
from typing import Optional

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


def get_pages(
    cutoff: Optional[datetime] = None, archive: bool = False
) -> QuerySet[BasePage]:
    """
    Returns a queryset of pages that may need to be archived.

    Pages are included if their `confirmed_needed_at` is older than the cutoff
    and their `last_published_at` is also older than the cutoff.
    By default, the cutoff is 1 year ago.

    If `archive` is True, the results are further filtered to include only
    pages for which an archive notification was sent 30 or more days ago —
    indicating the page has not been updated since the notification was sent.
    """
    if cutoff is None:
        cutoff = now() - timedelta(days=365)

    pages_qs = BasePage.objects.not_exact_type(*PAGES_TO_EXCLUDE).filter(
        Q(confirmed_needed_at__lt=cutoff) | Q(confirmed_needed_at__isnull=True),
        last_published_at__lt=cutoff,
        archive_notification_sent_at__gte=now() - timedelta(days=30)
    )

    if archive:
        pages_qs = pages_qs.filter(
            archive_notification_sent_at__lt=now() - timedelta(days=30)
        )

    return pages_qs


def confirm_needed(page: BasePage) -> None:
    page.confirmed_needed_at = now()
    page.save(update_fields=["confirmed_needed_at"])


def get_people_to_contact(page: BasePage) -> list[Person]:
    """
    Returns a unique list of people related to page in order of importance.
    """
    people = []

    content_owner = getattr(page, "content_owner", None)
    if content_owner and content_owner not in people:
        people.append(content_owner)

    if page.page_author and page.page_author not in people:
        people.append(page.page_author)

    latest_publisher = page.get_latest_publisher()
    if latest_publisher and latest_publisher.profile not in people:
        people.append(latest_publisher.profile)

    if page.owner and page.owner not in people:
        people.append(page.owner.profile)

    return people
