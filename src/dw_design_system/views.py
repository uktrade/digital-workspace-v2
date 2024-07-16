import json

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from dw_design_system.templatetags.dw_design_system import render_component
from dw_design_system.utils import CustomJSONDecoder, get_components, to_json


def components(request: HttpRequest) -> HttpResponse:
    components = []
    for component in get_components():
        new_component = component.copy()
        new_component.update(
            context_json=json.dumps(
                new_component["context"],
                indent=4,
                default=to_json,
            )
        )
        components.append(new_component)

    return render(
        request,
        "dw_design_system/components.html",
        {"components": components},
    )


def get_component(request: HttpRequest) -> HttpResponse:
    component_template = request.POST.get("template")
    new_context_str = request.POST.get("context")
    new_context = json.loads(new_context_str, cls=CustomJSONDecoder)
    component = next(
        (c for c in get_components() if c["template"] == component_template), None
    )

    if not component:
        return HttpResponse(status=404)

    context = component["context"]
    if new_context:
        context = new_context

    return HttpResponse(
        render_component(request, component["template"], context),
    )
