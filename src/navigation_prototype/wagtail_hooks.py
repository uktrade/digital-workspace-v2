from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from navigation_prototype.models import Nav


class NavAdmin(ModelAdmin):
    model = Nav
    menu_label = "Prototype nav"
    menu_icon = "link"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


modeladmin_register(NavAdmin)
