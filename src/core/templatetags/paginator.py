from django import template


register = template.Library()


@register.filter()
def get_elided_page_range(page):
    return page.paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)


@register.simple_tag(takes_context=True)
def get_pagination_url(context, page):
    request = context["request"]

    query_params = request.GET.copy()
    query_params["page"] = page

    return "?" + query_params.urlencode()
