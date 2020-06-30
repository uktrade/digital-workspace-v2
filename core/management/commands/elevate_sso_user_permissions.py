from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = "Elevate SSO user permissions for local development purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="Test user's email address",
            dest="email",
        )

    def handle(self, *args, **options):
        if settings.CAN_ELEVATE_SSO_USER_PERMISSIONS:
            email = options["email"]

            user = get_user_model()

            if email:
                sso_user = user.objects.get(
                    email=email,
                )
            else:
                sso_user = user.objects.exclude(
                    email="AnonymousUser",
                ).exclude(
                    Q(email__contains='test.com')
                ).first()
            sso_user.is_superuser = True
            sso_user.is_staff = True
            sso_user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully elevated user permission for user {}".format(
                        sso_user.email
                    )
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "The setting CAN_ELEVATE_SSO_USER_PERMISSIONS"
                    " is set to false, action not allowed"
                )
            )
