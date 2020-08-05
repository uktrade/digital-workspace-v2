from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)
from .models import (
    Comment,
    TopicTest,
    ThemeTest,
)


class CommentAdmin(ModelAdmin):
    model = Comment
    menu_label = 'Comment'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False  # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('content', 'author')
    list_filter = ('author',)
    search_fields = ('content', 'author')


class TopicTestAdmin(ModelAdmin):
    model = TopicTest
    menu_label = 'TopicTest'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False  # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)


class ThemeAdmin(ModelAdmin):
    model = ThemeTest
    menu_label = 'Theme'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False  # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)

# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(CommentAdmin)
modeladmin_register(TopicTestAdmin)
modeladmin_register(ThemeAdmin)
