from django import forms
from django.contrib import admin

from core.admin import admin_site
from extended_search.models import Setting
from extended_search.settings import extended_search_settings


class SettingAdminForm(forms.ModelForm):
    KEY_CHOICES = [(k, k) for k in extended_search_settings.all_keys]

    key = forms.ChoiceField(choices=KEY_CHOICES)

    class Meta:
        model = Setting
        fields = "__all__"


class SettingAdmin(admin.ModelAdmin):
    list_display = ["key", "value"]
    form = SettingAdminForm


admin_site.register(Setting, SettingAdmin)
