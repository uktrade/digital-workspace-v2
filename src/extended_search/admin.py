from django import forms
from django.contrib import admin

from core.admin import admin_site
from extended_search import settings
from extended_search.models import Setting


class SettingAdminForm(forms.ModelForm):
    key = forms.ChoiceField(choices=[])

    class Meta:
        model = Setting
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["key"].choices = [
            (k, k) for k in settings.extended_search_settings.all_keys
        ]


class SettingAdmin(admin.ModelAdmin):
    list_display = ["key", "value"]
    form = SettingAdminForm


admin_site.register(Setting, SettingAdmin)
