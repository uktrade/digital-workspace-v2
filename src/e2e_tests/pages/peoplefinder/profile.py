from .base import PeoplefinderPage


class ProfileViewPage(PeoplefinderPage):
    def goto_profile_edit_page(self):
        self.page.get_by_text("Edit profile").click()
        return ProfileEditPage(self.page)

    @property
    def full_name(self):
        return self.page.get_by_test_id("full-name").inner_text()

    @property
    def manager(self):
        return self.page.get_by_test_id("manager").inner_text()

    @property
    def roles(self):
        return [role.inner_text() for role in self.page.get_by_test_id("role").all()]

    @property
    def preferred_email(self):
        return self.page.get_by_test_id("preferred-email").inner_text()


class ProfileEditPage(PeoplefinderPage):
    def goto_profile_edit_team_page(self):
        self.page.get_by_text("Team and role").click()
        return ProfileEditPage(self.page)

    @property
    def first_name(self):
        return self.page.get_attribute("input[name=first_name]", "value")

    @first_name.setter
    def first_name(self, value):
        pass
        # first_name_input = self.driver.find_element_by_name("first_name")
        # first_name_input.clear()
        # first_name_input.send_keys(value)

    @property
    def manager(self):
        return self.page.get_by_test_id("current-manager").inner_text()

    @manager.setter
    def manager(self, value):
        pass
        # # TODO: Add support for picking a manager from the search results.

        # self.find_test_element("update-manager").click()
        # self.find_test_element("manager-search").send_keys(value)
        # self.find_test_element("select-manager").click()

    def add_role(self, job_title: str, head_of_team: bool):
        self.page.get_by_test_id("add-role").click()

        # The new role form should be the last one.
        formset = self.page.get_by_test_id("role-formset").last
        # Lets fill out the form.
        formset.get_by_test_id("job-title").fill(job_title)

        # The head_of_team input should default to false, so we only need to click it if
        # we need to set it to true.
        if head_of_team:
            formset.get_by_label("Head of team").click()

    def save_profile(self):
        self.page.get_by_test_id("save-profile").click()
        return ProfileViewPage(self.page)
