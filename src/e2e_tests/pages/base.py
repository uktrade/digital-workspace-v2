from playwright.sync_api import Page as PlaywrightPage


class Page:
    def __init__(self, page: PlaywrightPage) -> None:
        self.page = page

    def get_home_page(self):
        from .homepage import HomePage

        return HomePage(self.page)

    # def find_test_element(self, name: str) -> Locator:
    #     """A shortcut method for finding a element by the `data-testid="XXX"` attribute.

    #     Args:
    #         name: The name given to the element, e.g. "foo-bar" -> "data-testid="foo-bar""

    #     Returns:
    #         Locator: The matching web element.
    #     """
    #     return self.page.locator(f'data-testid="{name}"')

    # def find_test_elements(self, name: str) -> list[Locator]:
    #     """A shortcut method for finding elements by the `data-testid="XXX"` attribute.

    #     Args:
    #         name: The name given to the elements, e.g. "foo-bar" -> "data-testid="foo-bar""

    #     Returns:
    #         list[Locator]: A list of matching web elements.
    #     """
    #     return self.page.locator(f'data-testid="{name}"').all()


class SitePage(Page):
    def goto_wagtail_admin_page(self):
        self.page.locator("Go to Wagtail admin").click()

        from .wagtail_admin import WagtailAdminPage

        return WagtailAdminPage(self.page)

    def goto_profile_view_page(self):
        self.page.get_by_test_id("view-profile").click()

        from .peoplefinder.profile import ProfileViewPage

        return ProfileViewPage(self.page)
