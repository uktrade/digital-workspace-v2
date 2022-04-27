from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
@stringfilter
def preview(value):
    parts = value.split(" ")
    return " ".join(parts[0:40])
