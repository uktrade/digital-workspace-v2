from django.db.models import Count
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.panels import (
    FieldPanel,
    MultipleChooserPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.admin.ui.tables import Column
from wagtail.admin.widgets import PageListingButton
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import IndexView, SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from core.models import SiteAlertBanner, Tag
from core.models.external_links import ExternalLinkSetting
from core.models.tags import Campaign


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
    model = Tag
    menu_label = "Tags"
    panels = [
        FieldPanel("name"),
        MultipleChooserPanel(
            "taggedteam_set",
            label="Tagged teams",
            chooser_field_name="content_object",
        ),
        MultipleChooserPanel(
            "taggedperson_set",
            label="Tagged people",
            chooser_field_name="content_object",
        ),
        MultipleChooserPanel(
            "taggedpage_set",
            label="Tagged pages",
            chooser_field_name="content_object",
        ),
    ]
    icon = "tag"
    list_display = ["name", "link"]
    search_fields = ("name",)


register_snippet(TagsSnippetViewSet)


class CampaignTagsSnippetViewSet(TagsSnippetViewSet):
    model = Campaign
    menu_label = "Campaigns"
    add_to_admin_menu = True


register_snippet(CampaignTagsSnippetViewSet)


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
