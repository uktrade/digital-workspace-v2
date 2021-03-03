import uuid
from django.conf import settings
from django.test import TestCase

from user.test.factories import UserFactory

from user.backends import CustomAuthbrokerBackend
from user.models import User


class TestSSOUserProfile(TestCase):
    def setUp(self):
        self.sso_profile = {
            "email_user_id": "sso_test-1111111@test.com",
            "email": "sso_test@test.com",
            "contact_email": "sso_test_1@test.com",
            "first_name": "Barry",
            "last_name": "Test",
            "user_id": str(uuid.uuid4()),
        }

    def test_new_user_created(self):
        self.assertEqual(User.objects.count(), 0)

        CustomAuthbrokerBackend.get_or_create_user(
            self.sso_profile,
        )

        self.assertEqual(User.objects.count(), 1)

        user = User.objects.first()

        self.assertEqual(
            user.username,
            self.sso_profile["email_user_id"],
        )
        self.assertEqual(
            user.email,
            self.sso_profile["email"],
        )
        self.assertEqual(
            user.first_name,
            self.sso_profile["first_name"],
        )
        self.assertEqual(
            user.last_name,
            self.sso_profile["last_name"],
        )
        self.assertEqual(
            user.legacy_sso_user_id,
            self.sso_profile["user_id"],
        )

    def test_old_style_user_ignored(self):
        self.assertEqual(User.objects.count(), 0)

        sso_user_id = str(uuid.uuid4())

        UserFactory(
            username=sso_user_id,
            email="test@test.com",
            first_name="Deborah",
            last_name="Test",
            legacy_sso_user_id=None,
            sso_contact_email="test_1@test.com",
        )

        self.assertEqual(
            User.objects.first().username,
            sso_user_id,
        )

        profile = {
            "email_user_id": "deborah.test-1111111@test.com",
            "email": "test@test.com",
            "contact_email": "test_1@test.com",
            "first_name": "Deborah",
            "last_name": "Test",
            "user_id": sso_user_id,
        }

        CustomAuthbrokerBackend.get_or_create_user(profile)

        self.assertEqual(User.objects.count(), 2)

        self.assertEqual(
            User.objects.filter(username=profile["email_user_id"]).count(),
            1,
        )
