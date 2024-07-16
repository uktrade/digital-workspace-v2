from django import template
from django.shortcuts import render


register = template.Library()


@register.simple_tag(takes_context=True)
def render_component(context, template_name, component_context):
    component_template: template.Template = template.loader.get_template(template_name)
    component_context.update(context.flatten())
    return component_template.render(context=component_context)
