from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def icon_classes(context):
    icon_classes = []

    if context.get("small", False):
        icon_classes.append("small")

    if context.get("dark", False):
        icon_classes.append("dark")

    if context.get("hover_light", False):
        icon_classes.append("hover-light")

    if context.get("hover_dark", False):
        icon_classes.append("hover-dark")

    return " ".join(icon_classes)
