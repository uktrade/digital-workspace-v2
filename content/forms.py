from django import forms


class NewsCategoryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        from content.models import TaggedNews

        selected_category = kwargs.pop('selected_category', "")
        super(NewsCategoryForm, self).__init__(
            *args,
            **kwargs,
        )

        categories = []
        for category in TaggedNews.objects.all():
            categories.append(
                (category.tag.slug, category.tag)
            )

        categories.insert(0, ("", 'Select category'))

        self.fields['news_category'] = forms.ChoiceField(
            choices=categories,
            initial=selected_category,
        )
        self.fields["news_category"].widget.attrs.update(
            {
                "class": "govuk-select",
            },
        )

        self.fields["news_category"].widget.attrs["onchange"] = "this.form.submit();"


class CommentForm(forms.Form):
    comment = forms.CharField(
        label='Comment',
        max_length=255,
        required=True,
        widget=forms.Textarea(attrs={'class': 'govuk-textarea'})
    )
