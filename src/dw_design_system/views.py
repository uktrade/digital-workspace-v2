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
        "colours": [
            "--gds-red",
            "--dbt-red",
            "--dbt-blue",
            "--dbt-light-blue",
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
            "--text-xxxlarge",
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
        for template in get_dwds_templates(template_type):
            new_template = template.copy()
            new_template["request"] = request
            new_template.update(
                context_json=json.dumps(
                    new_template["context"],
                    indent=4,
                    default=to_json,
                )
            )
            templates.append(new_template)

        return render(
            request,
            "dw_design_system/dwds_components.html",
            {
                "template_type": template_type,
                "templates": templates,
            },
        )

    return templates


def get_dwds_template(template_type):
    def get_template(request: HttpRequest) -> HttpResponse:
        template_str = request.POST.get("template")
        new_context_str = request.POST.get("context")
        new_context = json.loads(new_context_str, cls=CustomJSONDecoder)
        template = next(
            (
                t
                for t in get_dwds_templates(template_type)
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

        return HttpResponse(
            render_component(request, template["template"], context),
        )

    return get_template


def layouts(request: HttpRequest) -> HttpResponse:
    layouts = [
        {
            "name": "Content stack",
            "template": "dwds/new/layouts/content_stack.html",
            "content_items": range(3),
        },
        {
            "name": "Content sidebar",
            "template": "dwds/new/layouts/content_sidebar.html",
            "content_items": range(2),
        },
        {
            "name": "Content grid",
            "template": "dwds/new/layouts/content_grid.html",
            "content_items": range(6),
        },
        {
            "name": "Content switcher",
            "template": "dwds/new/layouts/content_switcher.html",
            "content_items": range(3),
        },
        {
            "name": "Content custom sidebar",
            "template": "dwds/new/layouts/content_custom_sidebar.html",
        },
    ]

    return render(
        request,
        "dw_design_system/layouts.html",
        {"layouts": layouts},
    )
