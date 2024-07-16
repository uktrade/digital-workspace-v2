from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from wagtail.images.models import Image


def components(request: HttpRequest) -> HttpResponse:
    thumbnail_file = Image.objects.first()
    print("CAM WAS HERE")
    print(thumbnail_file)
    components = [
        {
            "name": "Banner Card",
            "template": "dwds/components/banner_card.html",
            "context": {
                "link": "https://www.gov.uk",
                "text": "This is a banner card for GOV.UK",
            },
        },
        {
            "name": "CTA Card",
            "template": "dwds/components/cta_card.html",
            "context": {
                "link": "https://www.gov.uk",
                "title": "This is a banner card for GOV.UK",
                "description": "This is a description for the CTA card",
            },
        },
        {
            "name": "Engagement Card",
            "template": "dwds/components/engagement_card.html",
            "context": {
                "is_highlighted": True,
                "url": "https://www.gov.uk",
                "title": "This is an engagement card for GOV.UK",
                "excerpt": "This is an excerpt for the engagement card",
                "author": "John Doe",
                "date": timezone.now(),
                "thumbnail": thumbnail_file,
            },
        },
        {
            "name": "Link List",
            "template": "dwds/components/link_list.html",
            "context": {},
        },
        {
            "name": "Navigation Card",
            "template": "dwds/components/navigation_card.html",
            "context": {},
        },
        {
            "name": "One Up Card",
            "template": "dwds/components/one_up_card.html",
            "context": {},
        },
    ]
    return render(
        request,
        "dw_design_system/components.html",
        {"components": components},
    )
