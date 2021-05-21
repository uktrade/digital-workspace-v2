from django import template

from core.models import SiteAlertBanner

register = template.Library()


@register.inclusion_tag("tags/site_alert.html")
def site_alert():
    active_site_alert = SiteAlertBanner.objects.filter(
        activated=True,
    ).first()

    if active_site_alert:
        return {
            "active_site_alert": active_site_alert,
        }

    return
