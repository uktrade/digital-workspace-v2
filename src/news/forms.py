from django import forms
from django.core.exceptions import ValidationError


class CommentForm(forms.Form):
    comment = forms.CharField(
        label="",
        max_length=500,
        required=True,
        widget=forms.Textarea(
            # Add classes
            attrs={"class": "dwds-textarea width-full"},
        ),
    )
    in_reply_to = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean_in_reply_to(self):
        from news.models import Comment

        in_reply_to = self.cleaned_data["in_reply_to"]

        if in_reply_to:
            if not in_reply_to.is_integer():
                raise ValidationError(
                    "Cannot save comment, provided id is not an integer"
                )

            original_comment = Comment.objects.filter(
                pk=in_reply_to,
            ).first()

            if not original_comment:
                raise ValidationError(
                    "Cannot save comment, cannot find comment that was replied to"
                )

        return in_reply_to
