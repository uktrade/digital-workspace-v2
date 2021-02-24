from django.core.exceptions import ValidationError
from django.test import TestCase

from content.models import SiteAlertBanner


class SiteAlertBannerTestCase(TestCase):
    def test_can_create_two_non_active_banners(self):
        SiteAlertBanner.objects.create(
            banner_text="test",
            activated=False,
        )

        SiteAlertBanner.objects.create(
            banner_text="test 1",
            activated=False,
        )

    def test_cannot_create_additional_active_banner(self):
        SiteAlertBanner.objects.create(
            banner_text="test",
            activated=True,
        )

        with self.assertRaises(ValidationError):
            SiteAlertBanner.objects.create(
                banner_text="test",
                activated=True,
            )

    def test_can_create_additional_inactive_banner(self):
        SiteAlertBanner.objects.create(
            banner_text="test",
            activated=True,
        )

        SiteAlertBanner.objects.create(
            banner_text="test",
            activated=False,
        )

    def test_cannot_activate_banner_whilst_other_active(self):
        SiteAlertBanner.objects.create(
            banner_text="test",
            activated=True,
        )

        second_banner = SiteAlertBanner.objects.create(
            banner_text="test",
            activated=False,
        )

        with self.assertRaises(ValidationError):
            second_banner.activated = True
            second_banner.save()
