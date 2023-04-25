from .base import SitePage


class HomePage(SitePage):
    def goto_profile_view_page(self):
        self.page.get_by_text("your profile").click()

        from .peoplefinder.profile import ProfileViewPage

        return ProfileViewPage(self.page)
