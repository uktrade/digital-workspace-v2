from .base import SitePage


class HomePage(SitePage):
    @property
    def bookmarks(self):
        return self.page.get_by_test_id("bookmark-link").all()
