from django.db.models import Count
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.admin.ui.tables import Column
from wagtail.admin.widgets import PageListingButton
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import IndexView, SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from core.models import SiteAlertBanner, Tag
from core.models.external_links import ExternalLinkSetting


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


class TagsSnippetViewSet(SnippetViewSet):
    panels = [
        FieldPanel("name"),
    ]
    model = Tag
    icon = "tag"
    add_to_admin_menu = True
    menu_label = "Tags"
    menu_order = 300
    list_display = ["name", Column("tagged_page_count"), "link"]
    search_fields = ("name",)

    def get_queryset(self, request):
        return self.model.objects.annotate(tagged_page_count=Count("taggedpage_set"))


register_snippet(TagsSnippetViewSet)


class PageInfoAdminButton(PageListingButton):
    label = _("Info")
    icon_name = "info-circle"
    aria_label_format = _("View info for '%(title)s'")
    url_name = "admin-page-info"

    @property
    def show(self):
        return self.user.has_perm("content.view_info_page")


@hooks.register("register_page_listing_more_buttons")
def page_listing_more_buttons(page, user, next_url=None):
    yield PageInfoAdminButton(
        page=page,
        next_url=next_url,
        user=user,
        priority=1,
    )


class ExternalLinkSettingIndexView(IndexView):
    def get_queryset(self):
        return super().get_queryset().order_by("external_link_text", "domain")


class ExternalLinkSettingViewSet(SnippetViewSet):
    model = ExternalLinkSetting
    icon = "info-circle"
    index_view_class = ExternalLinkSettingIndexView
    list_display = [
        "exclude",
        "domain",
        "external_link_text",
    ]
    list_per_page = 50
    inspect_view_enabled = True

    edit_handler = TabbedInterface(
        [
            ObjectList(
                [
                    FieldPanel("domain"),
                    FieldPanel("exclude"),
                    FieldPanel("external_link_text"),
                ],
                heading="Details",
            ),
        ]
    )


register_snippet(ExternalLinkSettingViewSet)
