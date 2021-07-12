from tests.utils import URL


class Page:
    def __init__(self, driver):
        self.driver = driver

    def get_home_page(self):
        self.driver.get(URL)

        from .homepage import HomePage

        return HomePage(self.driver)


class SitePage(Page):
    def goto_wagtail_admin_page(self):
        self.driver.find_element_by_link_text("Go to Wagtail admin").click()

        from .wagtail_admin import WagtailAdminPage

        return WagtailAdminPage(self.driver)
