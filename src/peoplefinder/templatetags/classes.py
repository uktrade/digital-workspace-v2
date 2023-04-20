from django import template


register = template.Library()


@register.simple_tag
def add_class(field, *classes) -> str:
    # `field.field` is needed as `field` is a `BoundField`
    field.field.widget.attrs["class"] = " ".join(
        [field.field.widget.attrs.get("class", ""), *classes]
    )

    return ""
