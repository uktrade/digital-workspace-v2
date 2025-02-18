from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def icon_classes(context):
    icon_classes = ["content-icon"]

    if context.get("small", False):
        icon_classes.append("small")

    if context.get("medium", False):
        icon_classes.append("medium")

    if context.get("dark", False):
        icon_classes.append("dark")

    if context.get("hover_light", False):
        icon_classes.append("hover-light")

    if context.get("hover_dark", False):
        icon_classes.append("hover-dark")

    return " ".join(icon_classes)
