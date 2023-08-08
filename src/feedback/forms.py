from crispy_forms_gds.layout import HTML, Field, Fieldset, Size
from django.forms import RadioSelect
from django_feedback_govuk.forms import SUBMIT_BUTTON, BaseFeedbackForm
from django_feedback_govuk.models import SatisfactionOptions

from feedback.models import SearchFeedbackV1


class SearchFeedbackV1Form(BaseFeedbackForm):
    class Meta:
        model = SearchFeedbackV1
        fields = ["satisfaction", "comment", "submitter"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["satisfaction"].label = ""
        self.fields["satisfaction"].required = True
        self.fields["satisfaction"].widget = RadioSelect()
        self.fields["satisfaction"].choices = SatisfactionOptions.choices
        self.fields["comment"].label = ""

        self.helper.layout.remove(SUBMIT_BUTTON)
        self.helper.layout.append(
            Fieldset(
                Field.radios(
                    "satisfaction",
                    template="django_feedback_govuk/widgets/star_rating/star_rating.html",
                ),
                legend="How do you feel about your search experience today?",
                legend_size=Size.MEDIUM,
            )
        )
        self.helper.layout.append(
            Fieldset(
                HTML(
                    "<p class='govuk-hint'>If you do not want to be contacted"
                    " about more research opportunities, you can let us know"
                    " here.</p>"
                ),
                Field("comment"),
                legend="Tell us why you gave that rating",
                legend_size=Size.MEDIUM,
            )
        )
        self.helper.layout.append(SUBMIT_BUTTON)
