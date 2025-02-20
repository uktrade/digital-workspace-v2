from django import template
from django.conf import settings


register = template.Library()


@register.inclusion_tag("tags/vwo_integration.html")
def vwo_integration():
    vwo_account = settings.VWO_ACCOUNT
    vwo_version = settings.VWO_VERSION
    
    return {"vwo_account": vwo_account, "vwo_version": vwo_version}