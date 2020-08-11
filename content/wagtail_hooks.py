from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)
from .models import (
    Comment,
    #Directorate,
    NewsCategory,
    Theme,
    Topic,
)


class CommentAdmin(ModelAdmin):
    model = Comment
    menu_label = 'Comment'  # ditch this to use verbose_name_plural from model
    menu_icon = 'doc-empty'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False  # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('content', 'author')
    list_filter = ('author',)
    search_fields = ('content', 'author')


class TopicAdmin(ModelAdmin):
    model = Topic
    menu_label = 'Topic'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False  # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)


class ThemeAdmin(ModelAdmin):
    model = Theme
    menu_label = 'Theme'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False  # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('theme',)
    list_filter = ('theme',)
    search_fields = ('theme',)


class NewsCategoryAdmin(ModelAdmin):
    model = NewsCategory
    menu_label = 'News Category'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False  # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('category',)
    list_filter = ('category',)
    search_fields = ('category',)


# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(CommentAdmin)
modeladmin_register(NewsCategoryAdmin)
modeladmin_register(ThemeAdmin)
modeladmin_register(TopicAdmin)
