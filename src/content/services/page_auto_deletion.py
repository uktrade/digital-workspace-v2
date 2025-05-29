from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils.timezone import now

from content.models import BasePage, BlogPost
from networks.models import NetworkContentPage
from news.models import NewsPage
from peoplefinder.models import Person
from working_at_dit.models import (
    Guidance,
    HowDoI,
    Policy,
)


PAGES_TO_INCLUDE = [
    BlogPost,
    Guidance,
    HowDoI,
    NetworkContentPage,
    NewsPage,
    Policy,
]


CUTOFF = now() - timedelta(days=365)

# do we need a env var if the cutoff is passed as a parameter?
# introduce another cutoff parameter for when the notification is sent (similar to the first one)?
# one for 365 days
# one for 30 days


def get_pages(
    pre_notification_cutoff: Optional[datetime] = None,
    post_notification_cutoff: Optional[datetime] = None,
    archive: bool = False,
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
    if pre_notification_cutoff is None:
        pre_notification_cutoff = now() - timedelta(days=settings.PAGE_AUTODELETION_PRE_NOTIFICATION_CUTOFF)

    if post_notification_cutoff is None:
        post_notification_cutoff = now() - timedelta(days=settings.PAGE_AUTODELETION_POST_NOTIFICATION_CUTOFF)

    pages_qs = BasePage.objects.exact_type(*PAGES_TO_INCLUDE).filter(
        Q(confirmed_needed_at__lt=pre_notification_cutoff)
        | Q(confirmed_needed_at__isnull=True),
        last_published_at__lt=pre_notification_cutoff,
        archive_notification_sent_at__gte=post_notification_cutoff,
    )

    if archive:
        pages_qs = pages_qs.filter(
            archive_notification_sent_at__lt=post_notification_cutoff
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
