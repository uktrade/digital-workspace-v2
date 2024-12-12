from django import template

from .templates_config import TEMPLATE_SECTIONS


register = template.Library()


@register.simple_tag(takes_context=True)
def render_dynamic_templates(context, page_type):
    matching_section = next(
        (section for section in TEMPLATE_SECTIONS if section["page_type"] == page_type),
        None,
    )
    if matching_section is None:
        return []

    return [
        action["render"]()
        for action in matching_section.get("actions", [])
        if action["is_visible"](context)
    ]
