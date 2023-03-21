from urllib.parse import urlparse

from django.utils.text import slugify

from peoplefinder.models import Team

from .base import PeoplefinderPage


class TeamViewPage(PeoplefinderPage):
    def goto_root_team_page(self) -> "TeamViewPage":
        url = urlparse(self.driver.current_url)
        new_url = url._replace(path="/teams")
        self.driver.get(new_url.geturl())

        return self

    def goto_team_page(self, team: Team) -> "TeamViewPage":
        url = urlparse(self.driver.current_url)
        new_url = url._replace(path=f"/teams/{slugify(team.name)}")
        self.driver.get(new_url.geturl())

        return self

    def goto_team_edit_page(self) -> "TeamEditPage":
        self.find_test_element("edit-team").click()

        return TeamEditPage(self.driver)

    @property
    def name(self) -> str:
        return self.find_test_element("name").text

    @property
    def abbreviation(self) -> str:
        return self.find_test_element("abbreviation").text

    @property
    def description(self) -> str:
        return self.find_test_element("description").text


class TeamEditPage(PeoplefinderPage):
    @property
    def name(self) -> str:
        return self.driver.find_element_by_name("name").get_attribute("value")

    @name.setter
    def name(self, value: str) -> None:
        name_input = self.driver.find_element_by_name("name")
        name_input.clear()
        name_input.send_keys(value)

    @property
    def abbreviation(self) -> str:
        return self.driver.find_element_by_name("abbreviation").get_attribute("value")

    @abbreviation.setter
    def abbreviation(self, value: str) -> None:
        abbreviation_input = self.driver.find_element_by_name("abbreviation")
        abbreviation_input.clear()
        abbreviation_input.send_keys(value)

    @property
    def description(self) -> str:
        return self.driver.find_element_by_name("description").get_attribute("value")

    @description.setter
    def description(self, value: str) -> None:
        description_input = self.driver.find_element_by_name("description")
        description_input.clear()
        description_input.send_keys(value)

    def save_team(self) -> TeamViewPage:
        self.find_test_element("save-team").click()

        return TeamViewPage(self.driver)
