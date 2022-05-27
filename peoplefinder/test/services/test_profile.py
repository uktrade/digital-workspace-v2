import pytest

from peoplefinder.models import Person
from peoplefinder.services.person import PersonService


class TestPersonService:
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


class TestCreateUserProfile:
    def test_already_has_profile(self, normal_user):
        profile = PersonService().create_user_profile(normal_user)

        assert normal_user.profile == profile

    @pytest.mark.parametrize(
        "profile_update",
        (
            # match on legacy_sso_user_id
            {"user": None},
            # match on email
            {"user": None, "legacy_sso_user_id": "not-a-match"},
            # match on first_name + last_name
            {
                "user": None,
                "legacy_sso_user_id": "not-a-match",
                "email": "not-a-match@example.com",
            },
        ),
    )
    def test_match(self, normal_user, profile_update):
        profile = normal_user.profile

        Person.objects.filter(pk=profile.pk).update(**profile_update)

        normal_user.refresh_from_db()

        assert not hasattr(normal_user, "profile")

        new_profile = PersonService().create_user_profile(normal_user)

        assert new_profile == profile
        assert hasattr(normal_user, "profile")
        assert normal_user.profile == profile

    def test_no_match(self, normal_user):
        profile = normal_user.profile

        profile.user = None
        profile.legacy_sso_user_id = "not-a-match"
        profile.email = "not-a-match@example.com"
        profile.first_name = "no"
        profile.last_name = "match"
        profile.save()

        assert not hasattr(normal_user, "profile")

        new_profile = PersonService().create_user_profile(normal_user)

        assert new_profile != profile
        assert hasattr(normal_user, "profile")
        assert normal_user.profile != profile
        assert normal_user.profile == new_profile
