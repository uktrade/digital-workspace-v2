import logging

from content.models.base_content import BasePage, ContentPage


logger = logging.getLogger(__name__)


class BlogIndex(BasePage):
    template = "content/blog_index.html"
    subpage_types = [
        "content.BlogPost",
    ]
    is_creatable = False

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["children"] = self.get_children().live().public().order_by("title")
        return context


class BlogPost(ContentPage):
    template = "content/blog_post.html"
    subpage_types = []
    is_creatable = True

    def get_template(self, request, *args, **kwargs):
        return self.template
