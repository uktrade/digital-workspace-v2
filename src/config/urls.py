from authbroker_client import urls as authbroker_client_urls
from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView
from django_feedback_govuk import urls as feedback_urls
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls

from core.admin import admin_site
from core.urls import urlpatterns as core_urlpatterns
from dw_design_system.urls import urlpatterns as dwds_urlpatterns
from events.views import ical_feed, ical_links
from peoplefinder.urls import api_urlpatterns, people_urlpatterns, teams_urlpatterns


urlpatterns = [
    # URLs for Staff SSO Auth broker
    path("auth/", include(authbroker_client_urls)),
    path(  # override Django admin set password page
        "django-admin/user/user/<int:user_id>/password/", RedirectView.as_view(url="/")
    ),
    # Django admin
    path("django-admin/", admin_site.urls),
    # Core
    path("core/", include(core_urlpatterns)),
    # Wagtail
    path("admin/login/", RedirectView.as_view(url="/")),  # override Wagtail login
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", include("search.urls")),
    path("pingdom/", include("pingdom.urls")),
    # Peoplefinder
    path("people/", include(people_urlpatterns)),
    path("teams/", include(teams_urlpatterns)),
    path(
        "people-and-teams/search/",
        RedirectView.as_view(
            url="/search/people",
            permanent=True,
            query_string=True,
        ),
        name="people-and-teams-search",
    ),
    path("peoplefinder/api/", include(api_urlpatterns)),
    path("sitemap.xml", sitemap),
    # Feedback
    path("feedback/", include(feedback_urls), name="feedback"),
    # Interactions
    path("interactions/", include("interactions.urls")),
    # Networks
    path("networks/", include("networks.urls")),
    # News
    path("news/", include("news.urls")),
    # DW Design System
    path("dwds/", include(dwds_urlpatterns)),
    # iCal feed for testing
    path("ical/", ical_links, name="ical_links"),
    path("ical/all/", ical_feed, name="ical_feed"),
]

# If django-silk is installed, add its URLs
if "silk" in settings.INSTALLED_APPS:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    if hasattr(settings, "DEV_TOOLS_ENABLED") and settings.DEV_TOOLS_ENABLED:
        # Dev tools purposefully only active with DEBUG=True clause
        urlpatterns += [
            path("dev-tools/", include("dev_tools.urls", namespace="dev_tools"))
        ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        # Django Debug Toolbar purposefully only active with DEBUG=True
        from debug_toolbar.toolbar import debug_toolbar_urls

        urlpatterns += debug_toolbar_urls()

urlpatterns += [
    # Wagtail
    path("", include(wagtail_urls)),
]


# Removed until we find a fix for Wagtail's redirect behaviour
handler404 = "core.views.view_404"
handler500 = "core.views.view_500"
handler403 = "core.views.view_403"
handler400 = "core.views.view_400"
