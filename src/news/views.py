from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from news.models import Comment
from news.services import comment as comment_service


@require_http_methods(["POST"])
def hide_comment(request: HttpRequest, pk: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=pk)
    if not comment_service.can_hide_comment(request.user, comment):
        return HttpResponseForbidden()
    comment_service.hide_comment(comment)
    return HttpResponse(status=200)
