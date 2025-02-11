import json
from django import template
from django.utils.html import mark_safe

from interactions.services import reactions as reactions_service
from django.contrib.contenttypes.models import ContentType


register = template.Library()


@register.simple_tag(takes_context=True)
def get_initial_page_data(context) -> str:
    request = context["request"]
    initial_page_data_v2 = {}

    for i, (k,v) in enumerate(context["FEATURE_FLAGS"].items()):
        initial_page_data_v2[f"feature_flag_{i+1}"] = f"{k}: {str(v).lower()}"

    # Page Data
    if "page" in context:
        page = context["page"]

        initial_page_data_v2["page_age_in_days"] = get_page_age_in_days(page)
        initial_page_data_v2["page_type"] = get_page_type(page)
        initial_page_data_v2["page_topics"] = " ".join(topic_title for topic_title in page.topic_titles)
        initial_page_data_v2["page_tags"] = get_page_tags(page)
        initial_page_data_v2["page_content_owner"] = page.content_owner.full_name if hasattr(page, "content_owner") else "NA"
        initial_page_data_v2["page_reactions"] = reactions_service.get_reaction_counts(page)

    # User Data
    initial_page_data_v2["user_profile_slug"] = str(request.user.profile.slug)

    for i, role in enumerate(request.user.profile.roles.all()):
        initial_page_data_v2[f"user_job_title_{i+1}"] = role.job_title
        initial_page_data_v2[f"user_team_slug_{i+1}"] = role.team.name.lower()

    initial_page_data_v2["user_professions"] = " ".join(profession.code for profession in request.user.profile.professions.all())
    initial_page_data_v2["user_grade"] = request.user.profile.grade.code if request.user.profile.grade else "NA"
    initial_page_data_v2["user_is_line_manager"] = str(request.user.profile.is_line_manager).lower()
    initial_page_data_v2["user_working_location"] = request.user.profile.get_office_location_display() if request.user.profile.get_office_location_display() else "NA"
    initial_page_data_v2["user_account_age_in_days"] = request.user.profile.days_since_account_creation()

    return mark_safe(json.dumps(initial_page_data_v2))


def get_page_age_in_days(page):
    page_age_in_days = page.days_since_last_published
    if page_age_in_days is not None:
        return page_age_in_days
    return "N/A"


def get_page_type(page):
    content_type = ContentType.objects.get_for_model(page)
    if content_type and hasattr(content_type, "name"):
        return content_type.name
    return "NA"


def get_page_tags(page):
    tag_set = []
    if hasattr(page, "tagged_items"):
        for tagged_item in page.tagged_items.select_related("tag").all():
            tag_set.append(tagged_item.tag.name)
    return tag_set if tag_set else ""