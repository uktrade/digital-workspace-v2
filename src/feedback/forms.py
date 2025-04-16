from crispy_forms_gds.layout import HTML, Button, Field, Fieldset, Size, Submit
from django.forms import HiddenInput, RadioSelect
from django_feedback_govuk.forms import SUBMIT_BUTTON, BaseFeedbackForm
from django_feedback_govuk.models import SatisfactionOptions

from feedback.models import HRFeedback, SearchFeedbackV1, SearchFeedbackV2


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


class HRFeedbackForm(BaseFeedbackForm):
    class Meta:
        model = HRFeedback
        fields = ["useful", "comment", "page_url", "contactable", "submitter"]
        widgets = {
            "useful": HiddenInput(),
            "page_url": HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["useful"].label = ""
        self.fields["comment"].label = ""
        self.fields["contactable"].label = (
            "Do you wish to be contacted for further research opportunities?"
        )
        self.fields["page_url"].label = ""

        self.helper.layout.remove(SUBMIT_BUTTON)
        self.helper.layout.append(
            Fieldset(
                legend="Providing feedback on your experience will help us improve the service",
                legend_size=Size.MEDIUM,
            )
        )
        self.helper.layout.append(Field("page_url"))
        self.helper.layout.append(Field("useful"))
        self.helper.layout.append(
            Fieldset(
                Field("comment"),
                Field("contactable"),
                legend="Why was this page not useful?",
                legend_size=Size.SMALL,
            )
        )
        self.helper.layout.append(SUBMIT_BUTTON)
        self.helper.layout.append(
            Button(
                "close",
                "Close feedback form",
                css_class="govuk-button--secondary",
                formmethod="dialog",
            )
        )


class SearchFeedbackV2Form(BaseFeedbackForm):
    class Meta:
        model = SearchFeedbackV2
        fields = [
            "search_query",
            "useful",
            "not_useful_comment",
            "trying_to_find",
            "search_data",
            "submitter",
        ]
        widgets = {
            "search_query": HiddenInput(),
            "useful": HiddenInput(),
            "search_data": HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["search_query"].label = ""
        self.fields["useful"].label = ""
        self.fields["not_useful_comment"].label = ""
        self.fields["trying_to_find"].label = ""

        self.helper.layout.remove(SUBMIT_BUTTON)
        self.helper.layout.append(Field("search_query"))
        self.helper.layout.append(Field("search_data"))
        self.helper.layout.append(Field("useful"))
        self.helper.layout.append(
            Fieldset(
                Field.textarea(
                    "not_useful_comment",
                    rows=6,
                ),
                legend="Why were the search results not useful?",
                legend_size=Size.MEDIUM,
            )
        )
        self.helper.layout.append(
            Fieldset(
                Field.textarea(
                    "trying_to_find",
                    rows=6,
                ),
                legend="Describe the information you were trying to find",
                legend_size=Size.MEDIUM,
            )
        )
        self.helper.layout.append(Submit("submit", "Submit feedback"))
        self.helper.layout.append(
            Button(
                "close",
                "Close feedback form",
                css_class="govuk-button--secondary",
                formmethod="dialog",
            )
        )
