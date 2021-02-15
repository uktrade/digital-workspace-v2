from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)

from home.models import (
    QuickLink,
    WhatsPopular,
)


class QuickLinksAdmin(ModelAdmin):
    model = QuickLink
    menu_label = "Quick links"
    menu_icon = "link"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


class WhatsPopularAdmin(ModelAdmin):
    model = WhatsPopular
    menu_label = "What's popular?"
    menu_icon = "link"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


modeladmin_register(QuickLinksAdmin)
modeladmin_register(WhatsPopularAdmin)
