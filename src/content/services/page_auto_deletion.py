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
from tools.models import Tool, ToolsHome
from user.models import User
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
        Q(confirmation_page_needed_at__lte=CUTOFF)
        | Q(confirmation_page_needed_at__isnull=True),
        last_published_at__lte=CUTOFF,
    )


def confirm_page_still_needed(page: BasePage) -> None:
    page.confirmation_page_needed_at = now()
    page.save(update_fields=["confirmation_page_needed_at"])


def get_pages_to_archive() -> QuerySet[BasePage]:
    return BasePage.objects.not_exact_type(*PAGES_TO_EXCLUDE).filter(
        Q(confirmation_page_needed_at_isnull=True)
        | Q(confirmation_page_needed_at__lte=CUTOFF),
        page_update_notified_at=now() - timedelta(days=30),
        last_published_at__lte=CUTOFF,
    )


def get_users_to_contact(page: BasePage) -> QuerySet[User]: ...
