from .base import SitePage


class HomePage(SitePage):
    def goto_profile_view_page(self):
        self.driver.find_element_by_css_selector("a.profile-link").click()

        from .peoplefinder.profile import ProfileViewPage

        return ProfileViewPage(self.driver)
