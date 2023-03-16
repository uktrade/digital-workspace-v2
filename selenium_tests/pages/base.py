# from selenium.webdriver.remote.webdriver import WebDriver
# from selenium.webdriver.remote.webelement import WebElement

# from selenium_tests.utils import URL


# class Page:
#     def __init__(self, driver: WebDriver) -> None:
#         self.driver = driver
#         self.driver.implicitly_wait(10)

#     def get_home_page(self):
#         self.driver.get(URL)

#         from .homepage import HomePage

#         return HomePage(self.driver)

#     def find_test_element(self, name: str) -> WebElement:
#         """A shortcut method for finding a element by the `data-test-XXX` attribute.

#         Args:
#             name: The name given to the element, e.g. "foo-bar" -> "data-test-foo-bar"

#         Returns:
#             WebElement: The matching web element.
#         """
#         return self.driver.find_element_by_css_selector(f"[data-test-{name}]")

#     def find_test_elements(self, name: str) -> list[WebElement]:
#         """A shortcut method for finding elements by the `data-test-XXX` attribute.

#         Args:
#             name: The name given to the elements, e.g. "foo-bar" -> "data-test-foo-bar"

#         Returns:
#             list[WebElement]: A list of matching web elements.
#         """
#         return self.driver.find_elements_by_css_selector(f"[data-test-{name}]")


# class SitePage(Page):
#     def goto_wagtail_admin_page(self):
#         self.driver.find_element_by_link_text("Go to Wagtail admin").click()

#         from .wagtail_admin import WagtailAdminPage

#         return WagtailAdminPage(self.driver)
