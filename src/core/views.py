import csv
import logging

from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic.base import View
from notifications_python_client.notifications import NotificationsAPIClient
from sentry_sdk import capture_exception
from waffle import flag_is_active
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.models import Page
from wagtail.search.backends import get_search_backend

from content.models import BasePage, ContentOwnerMixin
from core import flags
from core.forms import PageProblemFoundForm
from core.models import Tag
from interactions.services import tag_subscriptions as tag_sub_service
from user.models import User


logger = logging.getLogger(__name__)


def deactivated(request):
    return TemplateResponse(request, "core/deactivated.html", {}, status=403)


def view_404(request, exception):
    return TemplateResponse(
        request,
        "core/404.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=404,
    )


def view_500(request):
    return TemplateResponse(
        request,
        "core/500.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=500,
    )


def view_403(request, exception):
    capture_exception(exception)
    return TemplateResponse(
        request,
        "core/403.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=403,
    )


def view_400(request, exception):
    capture_exception(exception)
    return TemplateResponse(
        request,
        "core/400.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=400,
    )


def page_problem_found(request):
    message_sent = False

    if request.method == "POST":
        form = PageProblemFoundForm(request.POST)

        if form.is_valid():
            page_url = form.cleaned_data["page_url"]
            trying_to = form.cleaned_data["trying_to"]
            what_went_wrong = form.cleaned_data["what_went_wrong"]

            notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
            message_sent = notification_client.send_email_notification(
                email_address=settings.SUPPORT_REQUEST_EMAIL,
                template_id=settings.PAGE_PROBLEM_EMAIL_TEMPLATE_ID,
                personalisation={
                    "user_name": request.user.get_full_name(),
                    "user_email": request.user.email,
                    "page_url": page_url,
                    "trying_to": trying_to,
                    "what_went_wrong": what_went_wrong,
                },
            )
    else:
        form = PageProblemFoundForm()

    return TemplateResponse(
        request,
        "core/page_problem_found.html",
        {"form": form, "message_sent": message_sent},
    )


@require_GET
def user_groups_report(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    if not request.user.is_superuser:
        raise PermissionDenied

    header = ["ID", "Email", "First name", "Last name", "Groups"]

    qs = (
        User.objects.filter(groups__isnull=False)
        .annotate(group_names=StringAgg("groups__name", delimiter=", "))
        .values_list("id", "email", "first_name", "last_name", "group_names")
    )

    filename = "user_groups.csv"

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    writer = csv.writer(response)
    writer.writerow(header)
    for obj in qs:
        writer.writerow(obj)

    return response


@require_GET
def content_owners_report(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    if not request.user.is_superuser:
        raise PermissionDenied

    header = ["URL", "Content owner", "Content owner email", "Last updated"]
    results = [
        (
            p.get_full_url(request),
            p.content_owner.full_name if p.content_owner else "",
            p.content_contact_email,
            p.last_published_at,
        )
        for model in ContentOwnerMixin.get_all_subclasses()
        for p in model.objects.all().live().public()
    ]

    filename = "content_owners.csv"
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    writer = csv.writer(response)
    writer.writerow(header)
    for result in results:
        writer.writerow(result)

    return response


@require_GET
def tag_index(request: HttpRequest, slug: str) -> HttpResponse:
    if not flag_is_active(request, flags.TAG_INDEX):
        return HttpResponseForbidden()

    tag = get_object_or_404(Tag, slug=slug)
    tagged_teams, tagged_people, tagged_pages = tag_sub_service.get_tagged_content(
        tags=[tag]
    )
    context = {
        "page_title": f"{tag.name}",
        "tag": tag,
        "tagged_teams": tagged_teams[:6],
        "view_all_teams_url": reverse(
            "tag_content_index", kwargs={"slug": slug, "content_type": "teams"}
        ),
        "view_all_teams_text": f"View all '{tag.name}'teams",
        "tagged_people": tagged_people[:6],
        "view_all_people_url": reverse(
            "tag_content_index", kwargs={"slug": slug, "content_type": "people"}
        ),
        "view_all_people_text": f"View all '{tag.name}' people",
        "tagged_pages": tagged_pages[:6],
        "view_all_pages_url": reverse(
            "tag_content_index", kwargs={"slug": slug, "content_type": "pages"}
        ),
        "view_all_pages_text": f"View all '{tag.name}' pages",
        "is_subscribed_to_tag": tag_sub_service.is_subscribed(
            tag=tag, user=request.user
        ),
        "can_edit_tag": request.user.has_perm("core.change_tag"),
    }
    return TemplateResponse(request, "core/tag_index.html", context=context)


@require_GET
def tag_content_index(
    request: HttpRequest, slug: str, content_type: str
) -> HttpResponse:
    if not flag_is_active(request, flags.TAG_INDEX):
        return HttpResponseForbidden()

    if content_type not in ["people", "teams", "pages"]:
        raise Http404

    tag = get_object_or_404(Tag, slug=slug)
    match content_type:
        case "people":
            content_queryset = tag_sub_service.get_tagged_people(tags=[tag])
        case "teams":
            content_queryset = tag_sub_service.get_tagged_teams(tags=[tag])
        case "pages":
            content_queryset = tag_sub_service.get_tagged_pages(tags=[tag])
        case _:
            raise ValueError(f"Unable to get queryset for '{content_type}'")

    paginator = Paginator(content_queryset, 15)
    page = int(request.GET.get("page", 1))

    try:
        content_page = paginator.page(page)
    except EmptyPage:
        content_page = paginator.page(paginator.num_pages)

    context = {
        "page_title": f"{tag.name} {content_type}",
        "content_type": content_type,
        "tag": tag,
        "is_subscribed_to_tag": tag_sub_service.is_subscribed(
            tag=tag, user=request.user
        ),
        "can_edit_tag": request.user.has_perm("core.change_tag"),
        "content_page": content_page,
        "tag_index_url": reverse("tag_index", kwargs={"slug": slug}),
    }
    return TemplateResponse(request, "core/tag_content_listing.html", context=context)


class AdminInfoView(WagtailAdminTemplateMixin, View):
    template_name = "core/admin/pages/info.html"

    def get_page_title(self):
        return _("Editing %(page_type)s") % {
            "page_type": self.page_class.get_verbose_name()
        }

    def get_page_subtitle(self):
        return self.page.get_admin_display_title()

    def dispatch(self, request, page_id):
        self.page = get_object_or_404(Page.objects.all(), id=page_id).specific
        self.page_class = self.page.specific_class

        if not request.user.has_perm("content.view_info_page"):
            raise PermissionDenied

        return super().dispatch(request)

    def get(self, request):
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        annotated_page = (
            BasePage.objects.filter(pk=self.page.pk)
            .annotate_with_total_views()
            .annotate_with_unique_views_all_time()
            .annotate_with_unique_views_past_month()
            .first()
        )

        backend_name = settings.WAGTAILSEARCH_BACKENDS["default"]["BACKEND"]
        backend = get_search_backend(backend_name)
        mapping = backend.mapping_class(self.page_class)
        opensearch_document = mapping.get_document(self.page)

        context.update(
            page=self.page,
            total_page_views=annotated_page.total_views,
            total_unique_page_views=annotated_page.unique_views_all_time,
            unique_page_views_last_month=annotated_page.unique_views_past_month,
            opensearch_document=opensearch_document,
        )
        return context


def personal_feed(request: HttpRequest) -> HttpResponse:
    if not flag_is_active(request, flags.PERSONAL_FEED):
        return HttpResponseForbidden()

    context: dict[str, str] = {"page_title": "Your feed"}
    subscribed_tags = tag_sub_service.get_subscribed_tags(user=request.user)
    context.update(
        grouped_content=tag_sub_service.get_activity(tags=subscribed_tags),
    )
    return TemplateResponse(request, "core/personal_feed.html", context)
