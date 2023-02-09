from authbroker_client import urls as authbroker_client_urls
from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from core.admin import admin_site
from core.urls import urlpatterns as core_urlpatterns
from peoplefinder.urls import (
    api_urlpatterns,
    people_and_teams_urlpatterns,
    people_urlpatterns,
    teams_urlpatterns,
)
from search import views as search_views


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
    path("search/", search_views.search, name="search"),
    path("v2-search/", search_views.v2_search, name="v2-search"),
    path("pingdom/", include("pingdom.urls")),
    # Peoplefinder
    path("people/", include(people_urlpatterns)),
    path("teams/", include(teams_urlpatterns)),
    path("people-and-teams/", include(people_and_teams_urlpatterns)),
    path("peoplefinder/api/", include(api_urlpatterns)),
    path("sitemap.xml", sitemap),
    # Wagtail
    path("", include(wagtail_urls)),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Removed until we find a fix for Wagtail's redirect behaviour
handler404 = "core.views.view_404"
handler500 = "core.views.view_500"
handler403 = "core.views.view_403"
handler400 = "core.views.view_400"
