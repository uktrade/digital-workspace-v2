from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from wagtail.models import Page

from interactions.services import comments as comments_service
from news.forms import CommentForm
from news.models import Comment


@require_http_methods(["POST"])
def edit_comment(request: HttpRequest, *, comment_id):
    if not comments_service.can_edit_comment(request.user, comment_id):
        return HttpResponse(status=403)

    comment_message = request.POST.get("comment")
    try:
        comments_service.edit_comment(comment_id, comment_message)
    except comments_service.CommentNotFound:
        raise Http404

    return comments_service.get_comment_response(request, comment_id)


@require_http_methods(["GET"])
def get_page_comments(request: HttpRequest, *, pk):
    page = get_object_or_404(Page, id=pk).specific

    return comments_service.get_page_comments_response(request, page)


@require_http_methods(["GET"])
def get_comment(request: HttpRequest, *, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    return comments_service.get_comment_response(request, comment)


@require_http_methods(["GET"])
def edit_comment_form(request: HttpRequest, *, comment_id):
    if not comments_service.can_edit_comment(request.user, comment_id):
        return HttpResponse(status=403)

    comment = get_object_or_404(Comment, id=comment_id)
    comment_dict = comments_service.comment_to_dict(comment)

    comment_dict.update(
        edit_comment_form=CommentForm(initial={"comment": comment_dict["message"]}),
        edit_comment_url=reverse(
            "interactions:edit-comment",
            kwargs={
                "comment_id": comment_id,
            },
        ),
        edit_comment_cancel_url=reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment_id,
            },
        ),
    )

    return TemplateResponse(
        request,
        "interactions/edit_comment_form.html",
        context={
            "comment": comment_dict,
        },
    )


@require_http_methods(["POST"])
def reply_to_comment(request: HttpRequest, *, comment_id):
    if not comments_service.can_reply_comment(request.user, comment_id):
        return HttpResponse(status=403)

    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    comments_service.add_page_comment(
        comment.page,
        user,
        request.POST["comment"],
        request.POST.get("in_reply_to", comment_id),
    )

    return comments_service.get_comment_response(request, comment)


@require_http_methods(["POST"])
def comment_on_page(request: HttpRequest, *, pk):
    page = get_object_or_404(Page, id=pk).specific
    user = request.user

    comments_service.add_page_comment(
        page,
        user,
        request.POST["comment"],
        request.POST.get("in_reply_to", None),
    )

    return comments_service.get_page_comments_response(request, page)


@require_http_methods(["POST"])
def hide_comment(request: HttpRequest, pk: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=pk)
    if not comments_service.can_hide_comment(request.user, comment):
        return HttpResponseForbidden()

    comments_service.hide_comment(comment)

    return comments_service.get_page_comments_response(request, comment.page)
