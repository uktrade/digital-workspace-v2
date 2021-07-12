from .base import SitePage


class HomePage(SitePage):
    def goto_profile_page(self):
        self.driver.find_element_by_link_text("View your profile").click()

        from .profile import Profile

        return Profile(self.driver)
