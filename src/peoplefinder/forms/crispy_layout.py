from crispy_forms.layout import LayoutObject
from crispy_forms.utils import TEMPLATE_PACK
from crispy_forms_gds.layout import HTML, Field
from django.template.loader import render_to_string
from django.urls import reverse


class GovUKDetails(LayoutObject):
    template = "%s/layout/details.html"

    def __init__(self, *fields, summary=None, **kwargs):
        pre_fields_html_str = """
            <details class="govuk-details" data-module="govuk-details">
        """
        if summary:
            pre_fields_html_str += f"""
                <summary class="govuk-details__summary">
                    <span class="govuk-details__summary-text">
                        {summary}
                    </span>
                </summary>
            """
        pre_fields_html_str += """
            <div class="govuk-details__text">
        """
        pre_fields_html = HTML(pre_fields_html_str)
        post_fields_html = HTML("</div></details>")
        self.fields = [pre_fields_html] + list(fields) + [post_fields_html]

    def render(
        self,
        form,
        form_style,
        context,
        template_pack=TEMPLATE_PACK,
        extra_context=None,
        **kwargs,
    ):
        fields = self.get_rendered_fields(
            form, form_style, context, template_pack, **kwargs
        )

        template = self.get_template_name(template_pack)
        return render_to_string(template, {"fields": fields})


class TeamSelectField(Field):
    template = "%s/team-select-field.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.context.update(
            team_select_url=reverse("team-select"),
        )
