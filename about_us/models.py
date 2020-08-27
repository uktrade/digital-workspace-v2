from content.models import ContentPage


class AboutUsHome(ContentPage):
    is_creatable = False

    subpage_types = ["about_us.AboutUs"]


class AboutUs(ContentPage):
    is_creatable = True

    parent_page_types = ['about_us.AboutUsHome']
    subpage_types = ["about_us.AboutUs"]
