from wagtail import hooks

from .models import RecentPageView


@hooks.register("before_serve_page")
def update_recent_pages(page, request, serve_args, serve_kwargs):
    RecentPageView.objects.update_or_create(user=request.user, page=page)
