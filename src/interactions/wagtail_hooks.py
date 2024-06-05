from datetime import timedelta

from django.utils import timezone
from wagtail import hooks

from .models import RecentPageView


NEW_PAGE_VIEW_THRESHOLD = timedelta(minutes=5)


@hooks.register("before_serve_page")
def update_recent_pages(page, request, serve_args, serve_kwargs):
    rpv, created = RecentPageView.objects.get_or_create(user=request.user, page=page)

    # Increment the count if the page view already exists and the last view was
    # more than 5 minutes ago.
    if not created and rpv.updated_at + NEW_PAGE_VIEW_THRESHOLD < timezone.now():
        rpv.count += 1
        rpv.save(update_fields=["count"])
