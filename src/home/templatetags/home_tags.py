from django import template
from home import NEW_HOMEPAGE_FLAG
from waffle import flag_is_active


register = template.Library()


@register.inclusion_tag("home/tags/home_banner.html", takes_context=True)
def home_banner(context):
    request = context["request"]
    return {"using_new_homepage": flag_is_active(request, NEW_HOMEPAGE_FLAG)}
