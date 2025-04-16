from django.urls import path

from networks import views


app_name = "networks"

urlpatterns = [
    # TODO: Remove as part of INTR-517
    path(
        "convert-network/<int:pk>/to-content-page/",
        views.ConvertNetworkToNetworkContentPageView.as_view(),
        name="convert-network-to-content-page",
    ),
    # TODO: Remove as part of INTR-517
    path(
        "convert-network/<int:pk>/to-networks-home/",
        views.ConvertNetworkToNetworksHomeView.as_view(),
        name="convert-network-to-networks-home",
    ),
    # TODO: Remove as part of INTR-517
    path(
        "convert-network-content-page/<int:pk>/to-network/",
        views.ConvertNetworkContentPageToNetworkPageView.as_view(),
        name="convert-network-content-page-to-network",
    ),
]
