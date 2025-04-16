from crispy_forms.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Fieldset, Layout, Size

from peoplefinder.forms.crispy_layout import TeamSelectField


class RoleFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.layout = Layout(
            "person",
            Fieldset(
                TeamSelectField("team"),
                legend_size=Size.SMALL,
                legend="Team",
            ),
            Fieldset(
                Field(
                    "job_title",
                    data_testid="job-title",
                ),
                "head_of_team",
                legend_size=Size.SMALL,
                legend="Job title",
            ),
        )


class RoleFormsetFormHelper(RoleFormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.layout = Layout(
            Div(
                self.layout,
                # Add hidden field:
                Field("DELETE", type="hidden", data_formset_delete=""),
                Button(
                    "remove",
                    "Remove role",
                    size=Size.SMALL,
                    css_class="dwds-button--secondary",
                    data_formset_remove="",
                ),
                HTML(
                    """
                    <hr class="govuk-section-break govuk-section-break--l govuk-section-break--visible">
                    """
                ),
                data_formset_form="",
                data_testid="role-formset",
            ),
        )
