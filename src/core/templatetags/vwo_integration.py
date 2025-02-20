from django import template
from django.conf import settings


register = template.Library()


@register.inclusion_tag("tags/vwo_integration.html")
def vwo_integration():
    vwo_account_id = settings.VWO_ACCOUNT_ID
    vwo_version = settings.VWO_VERSION

    return {"vwo_account_id": vwo_account_id, "vwo_version": vwo_version}
