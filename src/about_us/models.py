from working_at_dit.models import PageWithTopics


class AboutUs(PageWithTopics):
    is_creatable = True

    parent_page_types = ["about_us.AboutUsHome", "about_us.AboutUs"]
    subpage_types = ["about_us.AboutUs"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        page = context["page"]
        context["children"] = (
            AboutUs.objects.live().public().child_of(page).order_by("title")
        )

        return context


class AboutUsHome(PageWithTopics):
    is_creatable = False

    subpage_types = ["about_us.AboutUs"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        page = context["page"]
        context["children"] = (
            AboutUs.objects.live().public().child_of(page).order_by("title")
        )

        return context
