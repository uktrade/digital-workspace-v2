from django import template


register = template.Library()


@register.inclusion_tag("dwds/components/feedback.html")
def feedback_sidebar(
    title="Give feedback", description="Did you find what you were looking for?"
):
    return {
        "title": title,
        "description": description,
    }
