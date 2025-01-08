from django import template
from wagtail.models import Page

from content.models import BasePage


register = template.Library()


@register.inclusion_tag("content/tags/page_side_menu.html", takes_context=True)
def page_side_menu(context):
    page = context.get("page")

    if not page or not isinstance(page, BasePage):
        return {}

    child_pages = Page.objects.child_of(page).order_by("title")

    return {
        "current_page": page,
        "sub_pages": [
            {"title": child_page.title, "url": child_page.url}
            for child_page in child_pages
        ],
        "enable_current_page_menu": True,
    }
