import json

from django import template
from django.utils.html import mark_safe
from wagtail.models import Page

from interactions.services import reactions as reactions_service


register = template.Library()


@register.simple_tag(takes_context=True)
def get_initial_page_data(context) -> str:
    request = context["request"]

    initial_page_data = {
        "page_age_in_days": "NA",
        "page_type": "NA",
        "page_topics": "",
        "page_tags": "",
        "page_content_owner": "NA",
        "page_reactions": {},
        "user_professions": "",
        "user_grade": "NA",
        "user_working_location": "NA",
    }

    for i, (k, v) in enumerate(context["FEATURE_FLAGS"].items()):
        initial_page_data[f"feature_flag_{i+1}"] = f"{k}: {str(v).lower()}"

    # Page Data
    if "page" in context and isinstance(context["page"], Page):
        page = context["page"]

        if (
            page_age_in_days := getattr(page, "days_since_last_published", None)
        ) is not None:
            initial_page_data["page_age_in_days"] = page_age_in_days

        if content_type := getattr(page, "content_type", None):
            initial_page_data["page_type"] = content_type.name

        if topic_titles := getattr(page, "topic_titles", None):
            initial_page_data["page_topics"] = " ".join(
                topic_title for topic_title in topic_titles
            )

        if tagged_items := getattr(page, "tagged_items", None):
            initial_page_data["page_tags"] = " ".join(
                tagged_item.tag.name
                for tagged_item in tagged_items.select_related("tag").all()
            )

        if content_owner := getattr(page, "content_owner", None):
            initial_page_data["page_content_owner"] = content_owner.full_name

        if page_reactions := reactions_service.get_page_reaction_counts(page):
            initial_page_data["page_reactions"] = page_reactions

    # User Data
    initial_page_data["user_profile_slug"] = str(request.user.profile.slug)

    for i, role in enumerate(request.user.profile.roles.all()):
        initial_page_data[f"user_team_slug_{i+1}"] = role.team.name.lower()
        initial_page_data[f"user_job_title_{i+1}"] = role.job_title

    if user_professions := request.user.profile.professions.all():
        initial_page_data["user_professions"] = " ".join(
            profession.code for profession in user_professions
        )

    if user_grade := request.user.profile.grade:
        initial_page_data["user_grade"] = user_grade.code

    initial_page_data["user_is_line_manager"] = request.user.profile.is_line_manager

    if location := request.user.profile.get_office_location_display():
        initial_page_data["user_working_location"] = location

    initial_page_data["user_account_age_in_days"] = (
        request.user.profile.days_since_account_creation()
    )

    return mark_safe(json.dumps(initial_page_data))  # noqa S308
