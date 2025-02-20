from django import template
from django.conf import settings


register = template.Library()


@register.inclusion_tag("tags/vwo_integration.html")
def vwo_integration():
    vwo_enabled = settings.VWO_ENABLED
    if not vwo_enabled:
        return {"vwo_enabled": vwo_enabled}

    return {
        "vwo_enabled": vwo_enabled,
        "vwo_account_id": settings.VWO_ACCOUNT_ID,
        "vwo_version": settings.VWO_VERSION,
    }
