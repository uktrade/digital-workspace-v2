from django import template

from core.utils import get_all_feature_flags


register = template.Library()


@register.inclusion_tag(filename="tags/js_feature_flag_object.html", takes_context=True)
def js_feature_flag_object(context):
    return {"feature_flags": get_all_feature_flags(context["request"])}
