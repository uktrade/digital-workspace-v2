import json

from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.html import mark_safe
from wagtail.models import Page

from interactions.services import reactions as reactions_service


register = template.Library()


@register.simple_tag(takes_context=True)
def get_initial_page_data(context) -> str:
    request = context["request"]
    initial_page_data = {}

    for i, (k, v) in enumerate(context["FEATURE_FLAGS"].items()):
        initial_page_data[f"feature_flag_{i+1}"] = f"{k}: {str(v).lower()}"

    # Page Data
    if "page" in context:
        page = context["page"]
        if isinstance(page, Page):
            initial_page_data["page_age_in_days"] = get_page_age_in_days(page)
            initial_page_data["page_type"] = get_page_type(page)
            initial_page_data["page_topics"] = " ".join(
                topic_title for topic_title in page.topic_titles
            )
            initial_page_data["page_tags"] = get_page_tags(page)
            initial_page_data["page_content_owner"] = (
                page.content_owner.full_name if hasattr(page, "content_owner") else "NA"
            )
            initial_page_data["page_reactions"] = reactions_service.get_reaction_counts(
                page
            )

    # User Data
    initial_page_data["user_profile_slug"] = str(request.user.profile.slug)

    for i, role in enumerate(request.user.profile.roles.all()):
        initial_page_data[f"user_team_slug_{i+1}"] = role.team.name.lower()
        initial_page_data[f"user_job_title_{i+1}"] = role.job_title

    initial_page_data["user_professions"] = " ".join(
        profession.code for profession in request.user.profile.professions.all()
    )
    initial_page_data["user_grade"] = (
        request.user.profile.grade.code if request.user.profile.grade else "NA"
    )
    initial_page_data["user_is_line_manager"] = request.user.profile.is_line_manager
    initial_page_data["user_working_location"] = (
        request.user.profile.get_office_location_display()
        if request.user.profile.get_office_location_display()
        else "NA"
    )
    initial_page_data["user_account_age_in_days"] = (
        request.user.profile.days_since_account_creation()
    )

    return mark_safe(json.dumps(initial_page_data))  # noqa S308


def get_page_age_in_days(page):
    page_age_in_days = page.days_since_last_published
    if page_age_in_days is not None:
        return page_age_in_days
    return "NA"


def get_page_type(page):
    content_type = ContentType.objects.get_for_model(page)
    if content_type and hasattr(content_type, "name"):
        return content_type.name
    return "NA"


def get_page_tags(page):
    if hasattr(page, "tagged_items"):
        page_tags = " ".join(
            tagged_item.tag.name
            for tagged_item in page.tagged_items.select_related("tag").all()
        )
    return page_tags if page_tags else ""
