from wagtail.core.models import Page


class HomePage(Page):
    is_creatable = False

    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(request, *args, **kwargs)
        #context['posts'] = self.posts
        #context['blog_page'] = self

        context['menu_items'] = self.get_children().filter(
            live=True,
            show_in_menus=True,
        )

        return context
