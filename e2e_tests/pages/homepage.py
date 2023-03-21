from .base import SitePage


class HomePage(SitePage):
    def goto_profile_view_page(self):
        self.page.locator("a.profile-link").click()

        from .peoplefinder.profile import ProfileViewPage

        return ProfileViewPage(self.page)
