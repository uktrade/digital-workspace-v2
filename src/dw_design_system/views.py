import json

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from dw_design_system.templatetags.dw_design_system import render_component
from dw_design_system.utils import (
    CustomJSONDecoder,
    get_dwds_templates,
    to_json,
)


def styles(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "DW Design System styles",
        "gds_colours": [
            "--gds-red",
            "--gds-yellow",
            "--gds-blue",
            "--gds-dark-blue",
            "--gds-green",
            "--gds-dark-green",
            "--gds-light-grey",
            "--gds-mid-grey",
            "--gds-dark-grey",
            "--gds-black",
            "--gds-purple",
        ],
        "dbt_colours": [
            "--dbt-red",
            "--dbt-blue",
            "--dbt-light-blue",
            "--dbt-white",
            "--dbt-miuk-light-grey",
        ],
        "spaces": [
            "--s5",
            "--s4",
            "--s3",
            "--s2",
            "--s1",
            "--s0",
            "--s-1",
            "--s-2",
            "--s-3",
            "--s-4",
            "--s-5",
        ],
        "text_sizes": [
            "--text-xxlarge",
            "--text-xlarge",
            "--text-large",
            "--text-medium",
            "--text-small",
        ],
    }

    return render(
        request,
        "dw_design_system/styles.html",
        context,
    )


def dwds_templates(template_type):
    def templates(request: HttpRequest) -> HttpResponse:
        templates = []
        for template in get_dwds_templates(template_type, request):
            new_template_context = template["context"].copy()

            if "request" in new_template_context:
                del new_template_context["request"]

            context_json = json.dumps(
                new_template_context,
                indent=4,
                default=to_json,
            )
            template.update(context_json=context_json)
            templates.append(template)

        return render(
            request,
            "dw_design_system/dwds_components.html",
            {
                "page_title": f"DW Design System { template_type }",
                "template_type": template_type,
                "templates": templates,
            },
        )

    return templates


def get_dwds_template(request: HttpRequest, template_type) -> HttpResponse:
    template_str = request.POST.get("template")
    new_context_str = request.POST.get("context")
    new_context = json.loads(new_context_str, cls=CustomJSONDecoder)
    template = next(
        (
            t
            for t in get_dwds_templates(template_type, request)
            if t["template"] == template_str
        ),
        None,
    )

    if not template:
        return HttpResponse(status=404)

    context = template["context"]
    if new_context:
        context = new_context

    context["request"] = request
    context["template_type"] = template_type
    context["page_title"] = f"DW Design System { template_type }"

    return HttpResponse(
        render_component(request, template["template"], context),
    )


def layouts(request: HttpRequest) -> HttpResponse:
    layouts = [
        {
            "name": "Content stack",
            "template": "dwds/layouts/content_stack.html",
            "content_items": range(3),
        },
        {
            "name": "Content sidebar",
            "template": "dwds/layouts/content_sidebar.html",
            "content_items": range(2),
        },
        {
            "name": "Content grid",
            "template": "dwds/layouts/content_grid.html",
            "content_items": range(6),
        },
        {
            "name": "Content switcher",
            "template": "dwds/layouts/content_switcher.html",
            "content_items": range(3),
        },
        {
            "name": "Content custom sidebar",
            "template": "dwds/layouts/content_custom_sidebar.html",
        },
        {
            "name": "Content spaced",
            "template": "dwds/layouts/content_spaced.html",
            "content_items": range(5),
        },
    ]

    return render(
        request,
        "dw_design_system/layouts.html",
        {
            "page_title": "DW Design System layouts",
            "layouts": layouts,
        },
    )
