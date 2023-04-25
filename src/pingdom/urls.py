from django.urls import path

from .views import pingdom


urlpatterns = [
    path("ping.xml", pingdom, name="pingdom"),
]
