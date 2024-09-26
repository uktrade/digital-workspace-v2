from django.forms import HiddenInput
from wagtail.models import Page


class ReadOnlyPageInput(HiddenInput):
    template_name = "core/forms/widgets/readonly_page.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update(
            display_value=Page.objects.get(id=value).title,
            id_for_label=attrs.get("id", None),
        )
        return context
