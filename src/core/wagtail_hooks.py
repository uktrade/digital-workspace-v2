from django.templatetags.static import static
from django.utils.html import format_html
from wagtail import hooks
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from core.models import SiteAlertBanner


class SiteAlertBannerAdmin(ModelAdmin):
    model = SiteAlertBanner
    menu_label = "Site alert banner"
    menu_icon = "warning"
    menu_order = 200
    add_to_settings_menu = True
    exclude_from_explorer = True
    list_display = ("banner_text", "activated")


modeladmin_register(SiteAlertBannerAdmin)


@hooks.register("insert_global_admin_css")
def global_admin_css():
    return format_html(
        '<link rel="stylesheet" href="{}">', static("stylesheets/wagtailtheme.css")
    )
