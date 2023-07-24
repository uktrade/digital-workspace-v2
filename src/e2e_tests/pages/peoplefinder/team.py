from django.utils.text import slugify

from peoplefinder.models import Team

from .base import PeoplefinderPage


class TeamViewPage(PeoplefinderPage):
    def goto_root_team_page(self) -> "TeamViewPage":
        self.page.goto("/teams/")
        return self

    def goto_team_page(self, team: Team) -> "TeamViewPage":
        self.page.goto(f"/teams/{slugify(team.name)}")
        return self

    def goto_team_edit_page(self) -> "TeamEditPage":
        self.page.get_by_test_id("edit-team").click()
        return TeamEditPage(self.page)

    @property
    def name(self) -> str:
        return self.page.get_by_test_id("name").inner_text()

    @property
    def abbreviation(self) -> str:
        return self.page.get_by_test_id("abbreviation").inner_text()

    @property
    def description(self) -> str:
        return self.page.get_by_test_id("description").inner_text()


class TeamEditPage(PeoplefinderPage):
    @property
    def name(self) -> str:
        return self.page.get_attribute("input[name=name]", "value")

    @name.setter
    def name(self, value: str) -> None:
        team_name_input = self.page.get_by_label("Team name (required)")
        team_name_input.fill(value)

    @property
    def abbreviation(self) -> str:
        return self.page.get_attribute("input[name=abbreviation]", "value")

    @abbreviation.setter
    def abbreviation(self, value: str) -> None:
        self.page.get_by_label("Team acronym or initials").fill(value)

    @property
    def description(self) -> str:
        return self.page.get_attribute("textarea[name=description]", "value")

    @description.setter
    def description(self, value: str) -> None:
        self.page.get_by_label("Team description").fill(value)

    def save_team(self) -> TeamViewPage:
        self.page.get_by_test_id("save-team").click()
        return TeamViewPage(self.page)
