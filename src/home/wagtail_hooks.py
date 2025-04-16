from wagtail_adminsortable.admin import SortableAdminMixin
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from home.models import HomeNewsOrder, QuickLink, WhatsPopular


class HomeNewsOrderAdmin(SortableAdminMixin, ModelAdmin):
    model = HomeNewsOrder
    menu_label = "Home news order"
    menu_icon = "link"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


class QuickLinksAdmin(ModelAdmin):
    model = QuickLink
    menu_label = "Quick links"
    menu_icon = "link"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


class WhatsPopularAdmin(ModelAdmin):
    model = WhatsPopular
    menu_label = "Popular on Digital Workspace"
    menu_icon = "link"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


modeladmin_register(HomeNewsOrderAdmin)
modeladmin_register(QuickLinksAdmin)
modeladmin_register(WhatsPopularAdmin)
