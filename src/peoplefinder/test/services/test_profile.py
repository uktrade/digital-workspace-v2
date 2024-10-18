import pytest
from django.conf import settings
from django.utils import timezone

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

    def test_notify_about_changes_debounce_no_delay(self, normal_user, mocker):
        mock_send_email_notification = mocker.patch(
            "peoplefinder.services.person.NotificationsAPIClient.send_email_notification"
        )

        normal_user.profile.edited_or_confirmed_at = timezone.now()
        normal_user.profile.save()

        PersonService().notify_about_changes_debounce(
            person_pk=normal_user.profile.pk,
            personalisation={},
            countdown=None,
        )
        mock_send_email_notification.assert_called_once_with(
            email_address=normal_user.profile.email,
            template_id=settings.PROFILE_EDITED_EMAIL_TEMPLATE_ID,
            personalisation={},
        )

    def test_notify_about_changes_debounce_with_delay(
        self, normal_user, mocker, freezer
    ):
        mock_send_email_notification = mocker.patch(
            "peoplefinder.services.person.NotificationsAPIClient.send_email_notification"
        )
        freezer.move_to("2023-08-01 12:00:00")

        normal_user.profile.edited_or_confirmed_at = timezone.now()
        normal_user.profile.save()

        PersonService().notify_about_changes_debounce(
            person_pk=normal_user.profile.pk,
            personalisation={},
            countdown=300,  # 5 minutes
        )
        mock_send_email_notification.assert_not_called()

        freezer.move_to("2023-08-01 12:03:00")
        PersonService().notify_about_changes_debounce(
            person_pk=normal_user.profile.pk,
            personalisation={},
            countdown=300,  # 5 minutes
        )
        mock_send_email_notification.assert_not_called()

        freezer.move_to("2023-08-01 12:05:00")
        PersonService().notify_about_changes_debounce(
            person_pk=normal_user.profile.pk,
            personalisation={},
            countdown=300,  # 5 minutes
        )
        mock_send_email_notification.assert_called_once_with(
            email_address=normal_user.profile.email,
            template_id=settings.PROFILE_EDITED_EMAIL_TEMPLATE_ID,
            personalisation={},
        )


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
                "email": "not-a-match@example.com",  # /PS-IGNORE
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
        profile.email = "not-a-match@example.com"  # /PS-IGNORE
        profile.first_name = "no"
        profile.last_name = "match"
        profile.save()

        assert not hasattr(normal_user, "profile")

        new_profile = PersonService().create_user_profile(normal_user)

        assert new_profile != profile
        assert hasattr(normal_user, "profile")
        assert normal_user.profile != profile
        assert normal_user.profile == new_profile
