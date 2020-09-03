from working_at_dit.models import PageWithTopics, PageTopic


class AboutUs(PageWithTopics):
    is_creatable = True

    parent_page_types = ['about_us.AboutUsHome']
    subpage_types = ["about_us.AboutUs"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["page_topics"] = PageTopic.objects.filter(
            page=self.pagewithtopics.contentpage,
        ).order_by("page__title")

        return context


class AboutUsHome(PageWithTopics):
    is_creatable = False

    subpage_types = ["about_us.AboutUs"]

    def get_context(self, request, *args, **kwargs):
        # TODO - should this only be 1 level of child pages deep?
        # It seems like the pages with child pages use a different format
        # which is more like the homepage
        context = super().get_context(request, *args, **kwargs)

        children = AboutUs.objects.all().order_by("title")

        context["children"] = children

        return context
