from peoplefinder.services.person import PersonService


class TestProfileService:
    def test_update_groups_and_permissions(self, normal_user):
        assert normal_user.groups.count() == 0
        assert normal_user.is_superuser is False

        PersonService.update_groups_and_permissions(
            person=normal_user.profile,
            is_person_admin=True,
            is_team_admin=True,
            is_superuser=True,
        )

        assert normal_user.groups.count() == 2
        assert normal_user.is_superuser is True
