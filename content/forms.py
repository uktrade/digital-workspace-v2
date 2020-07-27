from django import forms

from content.models import TaggedNews


class NewsCategoryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        selected_category = kwargs.pop('selected_category', "")
        super(NewsCategoryForm, self).__init__(
            *args,
            **kwargs,
        )
        test = TaggedNews.objects.all()

        categories = []
        for category in TaggedNews.objects.all():
            categories.append(
                (category.tag.slug, category.tag)
            )

        categories.insert(0, ("", 'Select category'))

        self.fields['news_categories'] = forms.ChoiceField(
            choices=categories,
            initial=selected_category
        )
        self.fields["news_categories"].widget.attrs.update(
            {
                "class": "govuk-select",
            }
        )
