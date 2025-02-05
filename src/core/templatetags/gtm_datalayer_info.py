import json
from django import template

from interactions.services import reactions as reactions_service
from django.contrib.contenttypes.models import ContentType


register = template.Library()


# Potential refactor for gtm_datalayer_info.html, fixed missing page_tags. TBC: page_topics
@register.simple_tag(takes_context=True)
def get_gtm_datalayer_info(context) -> str:
    request = context["request"]

    # What method is preffered here? Also, how should we retrieve the feature flags? context or get_all_feature_flags?
    # feature_flags = {f"feature_flag_{i+1}": f"{k}: {v}".lower() for i, (k, v) in enumerate(get_all_feature_flags(request).items())}
    feature_flags = {}
    for i, (k,v) in enumerate(context["FEATURE_FLAGS"].items()):
        feature_flags[f"feature_flag_{i+1}"] = f"{k}: {str(v).lower()}"
    
    last_published = 'NA'
    content_type_name = 'NA'
    # page_topics = 'NA'
    tag_set = []
    content_owner = 'NA'
    page_reactions = 'NA'

    if hasattr(context, "page"):
        page = context["page"]
        last_published = page.days_since_last_published

        content_type = ContentType.objects.get_for_model(page)
        content_type_name = content_type.name if content_type and hasattr(content_type, "name") else "NA"
        content_owner = page.content_owner.full_name if hasattr(page, "content_owner") else "NA"

        tag_set = []
        if hasattr(page, "tagged_items"):
            for tagged_item in page.tagged_items.select_related("tag").all():
                tag_set.append(tagged_item.tag.name)

        page_reactions = reactions_service.get_reaction_counts(page)

    # user_job_titles = {f"user_job_title_{i+1}": role.job_title for i, role in enumerate(request.user.profile.roles.all())}
    # user_team_slugs = {f"user_team_slug_{i+1}": role.team.name for i, role in enumerate(request.user.profile.roles.all())}
    user_job_titles = {}
    user_team_slugs = {}
    for i, role in enumerate(request.user.profile.roles.all()):
        user_job_titles[f"user_job_title_{i+1}"] = role.job_title
        user_team_slugs[f"user_team_slug_{i+1}"] = role.team.name
    user_working_location = request.user.profile.get_office_location_display()
    user_account_age_in_days = request.user.profile.days_since_account_creation()

    initial_page_data_v2 = {
        **feature_flags,

        # Page Data
        "page_age_in_days": last_published if last_published != None else "NA",
        "page_type": content_type_name if content_type_name else "NA",
        # "page_topics": "{% for topic in self.topics.all %}{{ topic.topic.title }} {% endfor %}",
        "page_tags": tag_set,
        "page_content_owner": content_owner if content_owner else "NA",
        "page_reactions": page_reactions,

        # User Data
        "user_profile_slug": str(request.user.profile.slug),
        # TBC - v1 returns the slug/title in lowercase, this returns it with title case (as is)
        **user_job_titles,
        **user_team_slugs,
        "user_professions": " ".join(profession.code for profession in request.user.profile.professions.all()),
        "user_grade": request.user.profile.grade.code if request.user.profile.grade else "NA",
        "user_is_line_manager": str(request.user.profile.is_line_manager).lower(),
        "user_working_location": user_working_location if user_working_location else "NA",
        "user_account_age_in_days": user_account_age_in_days,
    };

    context['initial_page_data_v2'] = json.dumps(initial_page_data_v2)

    return ""