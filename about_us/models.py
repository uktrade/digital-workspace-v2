from working_at_dit.models import PageWithTopics


class AboutUs(PageWithTopics):
    is_creatable = True

    parent_page_types = ["about_us.AboutUsHome"]
    subpage_types = ["about_us.AboutUs"]


class AboutUsHome(PageWithTopics):
    is_creatable = False

    subpage_types = ["about_us.AboutUs"]
