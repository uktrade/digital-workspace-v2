from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from news.models import Comment, NewsCategory


class CommentAdmin(ModelAdmin):
    model = Comment
    menu_label = "Comments"  # ditch this to use verbose_name_plural from model
    menu_icon = "doc-empty"  # change as required
    menu_order = 300  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = (
        "content",
        "author",
        "legacy_author_name",
    )
    search_fields = (
        "content",
        "legacy_author_name",
        "legacy_author_email",
        "author__first_name",
        "author__last_name",
        "author__email",
    )


class NewsCategoryAdmin(ModelAdmin):
    model = NewsCategory
    menu_label = "News Categories"  # ditch this to use verbose_name_plural from model
    menu_icon = "tag"  # change as required
    menu_order = 300  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = (
        "category",
        "lead_story",
    )
    list_filter = ("category",)
    search_fields = ("category",)


# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(CommentAdmin)
modeladmin_register(NewsCategoryAdmin)
