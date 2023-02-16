import os

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag
def git_info():
    APP_ENV = os.environ.get("APP_ENV", "-")
    GIT_BRANCH = os.environ.get("GIT_BRANCH", "-")
    GIT_COMMIT = os.environ.get("GIT_COMMIT", "-")
    return mark_safe(  # noqa S703 S308
        f"<!-- env: {APP_ENV} // git_branch: {GIT_BRANCH} // "
        f"git_commit: {GIT_COMMIT} -->"
    )
