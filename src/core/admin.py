from django.contrib.admin import AdminSite
from django.http import HttpResponseRedirect
from django.urls import reverse
from waffle.admin import FlagAdmin as WaffleFlagAdmin

from core.models import FeatureFlag


class DigitalWorkspaceAdminSite(AdminSite):
    site_header = "Digital Workspace Administration"

    def login(self, request, extra_context=None):
        if request.user.is_authenticated:
            if request.user.is_staff:
                index_path = reverse(
                    "admin:index",
                    current_app=self.name,
                )
                return HttpResponseRedirect(index_path)

        return HttpResponseRedirect("/")


admin_site = DigitalWorkspaceAdminSite(name="dw_admin")
admin_site.register(FeatureFlag, WaffleFlagAdmin)
