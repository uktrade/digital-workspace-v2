from django import template

register = template.Library()


@register.inclusion_tag("tags/cookie_banner.html", takes_context=True)
def cookie_banner(context):
    request = context["request"]
    seen_cookie_banner = request.COOKIES.get("seen_cookie_banner")
    return {
        "seen_cookie_banner": seen_cookie_banner,
    }
