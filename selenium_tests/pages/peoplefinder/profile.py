import time

from .base import PeoplefinderPage


class ProfileViewPage(PeoplefinderPage):
    def goto_profile_edit_page(self):
        self.driver.find_element_by_link_text("Edit profile").click()

        return ProfileEditPage(self.driver)

    @property
    def full_name(self):
        return self.find_test_element("full-name").text

    @property
    def manager(self):
        return self.find_test_element("manager").text

    @property
    def roles(self):
        return [element.text for element in self.find_test_elements("role")]

    @property
    def preferred_email(self):
        return self.find_test_element("preferred-email").text


class ProfileEditPage(PeoplefinderPage):
    @property
    def first_name(self):
        return self.driver.find_element_by_name("first_name").get_attribute("value")

    @first_name.setter
    def first_name(self, value):
        first_name_input = self.driver.find_element_by_name("first_name")
        first_name_input.clear()
        first_name_input.send_keys(value)

    @property
    def manager(self):
        return self.find_test_element("current-manager").text

    @manager.setter
    def manager(self, value):
        # TODO: Add support for picking a manager from the search results.

        self.find_test_element("update-manager").click()
        self.find_test_element("manager-search").send_keys(value)
        self.find_test_element("select-manager").click()

    def add_role(self, job_title: str, head_of_team: bool):
        # TODO: Add support for changing the team.

        role_forms = self._find_role_forms()

        self.find_test_element("add-role").click()
        # The new role form should be the last one.
        form = self._wait_for_new_role_form(role_forms)
        # Lets fill out the form.
        form.find_element_by_name("job_title").send_keys(job_title)

        # The head_of_team input should default to false, so we only need to click it if
        # we need to set it to true.
        if head_of_team:
            form.find_element_by_name("head_of_team").click()

        self.find_test_element("save-role").click()

    def save_profile(self):
        self.find_test_element("save-profile").click()

        return ProfileViewPage(self.driver)

    def _wait_for_new_role_form(self, current_role_forms):
        retries = 10

        while retries > 0:
            forms = self._find_role_forms()

            if len(forms) > len(current_role_forms):
                return forms[-1]

            # 50ms
            time.sleep(0.05)
            retries -= 1

        raise Exception("No new role form found")

    def _find_role_forms(self):
        return self.find_test_elements("role-form")
