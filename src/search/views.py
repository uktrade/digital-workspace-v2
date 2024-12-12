import csv
import logging

import sentry_sdk
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from config import settings
from content.models import BasePage, ContentPage
from extended_search.models import Setting as SearchSetting
from extended_search.settings import settings_singleton
from news.models import NewsPage
from peoplefinder.models import Person, Team
from search.templatetags import search as search_template_tag
from search.utils import get_query_info_for_model


logger = logging.getLogger(__name__)


def can_view_explore():
    return user_passes_test(lambda u: u.has_perm("extended_search.view_explore"))


def can_export_search():
    return user_passes_test(lambda u: u.has_perm("extended_search.export_search"))


@require_http_methods(["GET"])
def autocomplete(request: HttpRequest) -> HttpResponse:
    _category = "autocomplete"
    query = request.GET.get("query", "")
    page = "1"

    search_results = search_template_tag.autocomplete(request, query)

    context = {
        "search_url": reverse("search:autocomplete"),
        "search_query": query,
        "search_category": _category,
        "search_results": list(
            search_results["pages"] + search_results["people"] + search_results["teams"]
        ),
        "pages": search_results["pages"],
        "pages_count": len(search_results["pages"]),
        "people": search_results["people"],
        "people_count": len(search_results["people"]),
        "teams": search_results["teams"],
        "teams_count": len(search_results["teams"]),
        "page": page,
        "search_feedback_initial": {
            "search_query": query,
            "search_data": {"category": _category},
        },
    }

    return TemplateResponse(
        request, "search/partials/result/autocomplete_page.html", context=context
    )


@require_http_methods(["GET"])
def search(request: HttpRequest, category: str | None = None) -> HttpResponse:
    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")
    tab_override = request.GET.get("tab_override", False)

    # If the category is invalid, redirect to search all.
    if category not in search_template_tag.SEARCH_CATEGORIES:
        return redirect(
            reverse("search:category", kwargs={"category": "all"}) + f"?query={query}"
        )

    context = {
        "search_url": reverse("search:category", args=[category]),
        "search_query": query,
        "tab_override": tab_override,
        "search_category": category,
        "page": page,
        "search_feedback_initial": {
            "search_query": query,
            "search_data": {"category": category},
        },
    }

    # https://docs.sentry.io/platforms/python/performance/instrumentation/custom-instrumentation/#accessing-the-current-transaction
    transaction = sentry_sdk.Hub.current.scope.transaction

    if transaction is not None:
        transaction.set_tag("search.category", category)
        transaction.set_tag("search.query", query)
        transaction.set_tag("search.page", page)

    return TemplateResponse(request, "search/search.html", context=context)


@can_view_explore()
def explore(request: HttpRequest) -> HttpResponse:
    """
    Administrative view for exploring search options, boosts, etc
    """
    if request.method == "POST":
        if not request.user.has_perm("extended_search.change_setting"):
            messages.error(request, "You are not authorised to edit settings")

        key = request.POST.get("key")
        value = request.POST.get("value")

        SearchSetting.objects.update_or_create(key=key, defaults={"value": value})
        messages.info(request, f"Setting '{key}' saved")

    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")

    boost_vars = [
        {"name": k, "value": settings_singleton[k]}
        for k in settings_singleton.all_keys()
        if "boost_parts" in k
    ]

    subqueries = {
        "pages": get_query_info_for_model(ContentPage, query),
        "people": get_query_info_for_model(Person, query),
        "teams": get_query_info_for_model(Team, query),
    }

    context = {
        "search_url": reverse("search:explore"),
        "search_query": query,
        "search_category": "all",
        "page": page,
        "boost_variables": boost_vars,
        "sub_queries": subqueries,
    }

    return TemplateResponse(request, "search/explore.html", context=context)


@can_export_search()
def export_search(request: HttpRequest, category: str) -> HttpResponse:
    """
    Administrative view for exporting search results as csv
    """
    query = request.GET.get("query", "")
    if category == "all":
        category = "all_pages"
    search_vector = search_template_tag.SEARCH_VECTORS[category](request)
    search_results = search_vector.search(query)
    search_model = search_vector.model

    def build_search_export_csv_response(
        request: HttpRequest, category, search_model, search_results
    ) -> HttpResponse:
        header = build_export_search_csv_header(search_model)

        if issubclass(search_model, BasePage):
            return build_page_export_csv_response(
                request, category, header, search_results
            )

        if issubclass(search_model, Person):
            return build_people_export_csv_response(
                request, category, header, search_results
            )

        if issubclass(search_model, Team):
            return build_teams_export_csv_response(
                request, category, header, search_results
            )

    def build_export_search_csv_header(search_model) -> list[str]:
        if issubclass(search_model, BasePage):
            return [
                "Title",
                "URL",
                "Edit-URL",
                "Content-Owner-Name",
                "Content-Owner-Email",
                "Content-Author-Name",
                "Content-Author-Email",
                "First-Published",
                "Last-Updated",
                "Page-Type",
            ]

        if issubclass(search_model, Person):
            return [
                "Name",
                "Email",
                "Phone",
                "Profile-URL",
                "Roles{'Job-Title':'Team-Name'}",
            ]

        if issubclass(search_model, Team):
            return [
                "Title",
                "URL",
                "Edit-URL",
            ]

    def build_search_export_response_header(category: str) -> HttpResponse:
        filename = f"search_export_{category}.csv"
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
        return response

    def build_page_export_csv_response(
        request, category, header, search_results
    ) -> HttpResponse:
        response = build_search_export_response_header(category)
        base_url = get_base_url(request)

        writer = csv.writer(response)
        writer.writerow(header)

        for result in search_results:
            content_owner = get_content_owner(result)
            content_author = get_content_author(result)
            row = [
                result.title,
                result.get_full_url(),
                get_edit_page_url(base_url, result),
                content_owner["name"],
                content_owner["email"],
                content_author["name"],
                content_author["email"],
                result.first_published_at,
                result.last_published_at,
                type(result).__name__,
            ]
            writer.writerow(row)
        return response

    def get_base_url(request: HttpRequest) -> str:
        return f"{request.scheme}://{request.get_host()}"

    def get_edit_page_url(base_url, page) -> str:
        return f"{base_url}{reverse('wagtailadmin_pages:edit', args=[page.id])}"

    def get_content_owner(page) -> dict:
        content_owner = {}
        if hasattr(page, "content_owner"):
            content_owner["name"] = page.content_owner.full_name
            content_owner["email"] = page.content_owner.email
        else:
            content_owner["name"] = ""
            content_owner["email"] = ""
        return content_owner

    def get_content_author(page) -> dict:
        content_author = {}
        perm_sec_as_author = (
            page.perm_sec_as_author if hasattr(page, "perm_sec_as_author") else False
        )
        if perm_sec_as_author:
            content_author["name"] = settings.PERM_SEC_NAME
            content_author["email"] = ""
        elif issubclass(page.__class__, NewsPage):
            if hasattr(page, "get_first_publisher"):
                content_author["name"] = page.get_first_publisher().get_full_name()
                content_author["email"] = page.get_first_publisher().email
        else:
            content_author["name"] = page.get_latest_revision().user.get_full_name()
            content_author["email"] = page.get_latest_revision().user.email
        return content_author

    def build_people_export_csv_response(
        request, category, header, search_results
    ) -> HttpResponse:
        response = build_search_export_response_header(category)
        base_url = get_base_url(request)

        writer = csv.writer(response)
        writer.writerow(header)

        for result in search_results:
            row = [
                f"{result.first_name} {result.last_name}",
                result.email,
                result.primary_phone_number,
                f"{base_url}{result.get_absolute_url()}",
                {role.job_title: role.team.name for role in result.roles.all()},
            ]
            writer.writerow(row)
        return response

    def build_teams_export_csv_response(
        request, category, header, search_results
    ) -> HttpResponse:
        response = build_search_export_response_header(category)
        base_url = get_base_url(request)

        writer = csv.writer(response)
        writer.writerow(header)

        for result in search_results:
            row = [
                result.name,
                f"{base_url}{result.get_absolute_url()}",
                f"{base_url}{result.get_absolute_url()}edit",
            ]
            writer.writerow(row)
        return response

    return build_search_export_csv_response(
        request, category, search_model, search_results
    )
