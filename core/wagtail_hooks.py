from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)

from core.models import (
    SiteAlertBanner,
)

from wagtail.documents.models import Document as WagtailDocument


class SiteAlertBannerAdmin(ModelAdmin):
    model = SiteAlertBanner
    menu_label = "Site alert banner"
    menu_icon = "warning"
    menu_order = 200
    add_to_settings_menu = True
    exclude_from_explorer = True
    list_display = ("banner_text", "activated")


class WagtailDocumentAdmin(ModelAdmin):
    model = WagtailDocument
    menu_label = "Document admin"
    menu_icon = "doc-empty-inverse"
    menu_order = 200
    add_to_settings_menu = True
    exclude_from_explorer = True
    list_display = ("title", "created_at", "uploaded_by_user")


modeladmin_register(SiteAlertBannerAdmin)
modeladmin_register(WagtailDocumentAdmin)
