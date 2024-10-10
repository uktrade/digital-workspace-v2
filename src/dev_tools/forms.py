from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()


def get_user_choices():
    return [
        (None, "AnonymousUser"),
        *[(x.id, str(x)) for x in User.objects.all()],
    ]


class ChangeUserForm(forms.Form):
    user = forms.ChoiceField(choices=get_user_choices, required=False)
