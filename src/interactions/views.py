from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods
from wagtail.models import Page

from . import get_bookmarks, is_page_bookmarked
from .models import Bookmark
from .templatetags.bookmarks import bookmark_page_input


@require_http_methods(["POST"])
def bookmark(request, *args, **kwargs):
    user = request.user

    if request.method == "POST":
        page_id = int(request.POST["page_id"])

        page = get_object_or_404(Page, id=page_id)
        bookmark = not is_page_bookmarked(user, page)

        if bookmark:
            Bookmark.objects.get_or_create(user=user, page=page)
        else:
            Bookmark.objects.get(user=user, page=page).delete()

        return TemplateResponse(
            request,
            "interactions/bookmark_page_input.html",
            bookmark_page_input(user, page),
        )


@require_http_methods(["DELETE"])
def remove_bookmark(request, pk, *args, **kwargs):
    Bookmark.objects.get(pk=pk, user=request.user).delete()

    return HttpResponse()


@require_http_methods(["GET"])
def bookmark_index(request, *args, **kwargs):
    context = {"bookmarks": get_bookmarks(request.user)}

    return TemplateResponse(
        request,
        "interactions/bookmark_index.html",
        context=context,
    )
