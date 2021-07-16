from urllib.parse import urlparse

from .base import PeoplefinderPage


class TeamViewPage(PeoplefinderPage):
    def goto_root_team_page(self):
        url = urlparse(self.driver.current_url)
        new_url = url._replace(path="/teams")
        self.driver.get(new_url.geturl())

        return self

    @property
    def description(self):
        return self.find_test_element("description").text
