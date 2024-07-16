from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def components(request: HttpRequest) -> HttpResponse:
    components = [
        (
            "dwds/components/banner_card.html",
            {},
        ),
        (
            "dwds/components/cta_card.html",
            {},
        ),
        (
            "dwds/components/engagement_card.html",
            {},
        ),
        (
            "dwds/components/link_list.html",
            {},
        ),
        (
            "dwds/components/navigation_card.html",
            {},
        ),
        (
            "dwds/components/one_up_card.html",
            {},
        ),
    ]
    return render(
        request,
        "dw_design_system/components.html",
        {"components": components},
    )
