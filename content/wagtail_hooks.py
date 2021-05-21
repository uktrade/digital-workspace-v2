from django.templatetags.static import static
from django.utils.html import format_html
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)
from wagtail.core import hooks

from content.models import (
    Theme,
)


class ThemeAdmin(ModelAdmin):
    model = Theme
    menu_label = "Theme"  # ditch this to use verbose_name_plural from model
    menu_icon = "tag"  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("title",)
    list_filter = ("title",)
    search_fields = ("title",)


modeladmin_register(ThemeAdmin)


@hooks.register("construct_page_action_menu")
def remove_submit_to_moderator_option(menu_items, request, context):
    # TODO - remove delete page item

    menu_items[:] = [item for item in menu_items if item.name != "action-submit"]


@hooks.register("insert_global_admin_css")
def global_admin_css():
    static_path = static("wagtail_admin_augmentation.css")
    return format_html(
        f'<link rel="stylesheet" href="{static_path}">',
    )
