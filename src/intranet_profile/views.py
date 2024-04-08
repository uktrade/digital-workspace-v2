from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from wagtail.models import Page

from . import is_page_bookmarked
from .models import Bookmark
from .templatetags.bookmarks import bookmark_page


def bookmark(request, *args, **kwargs):
    user = request.user

    if request.method == "POST":
        page_id = int(request.POST["page_id"])

        page = get_object_or_404(Page, id=page_id)
        bookmark = not is_page_bookmarked(user, page)

        if bookmark:
            Bookmark.objects.get_or_create(profile=user.intranet, page=page)
        else:
            Bookmark.objects.get(profile=user.intranet, page=page).delete()

        return TemplateResponse(
            request,
            "intranet_profile/bookmark_page.html",
            bookmark_page(user, page),
        )
