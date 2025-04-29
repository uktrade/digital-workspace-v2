import factory

from user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.fuzzy.FuzzyText(length=12)
    last_name = factory.fuzzy.FuzzyText(length=12)
    email = legacy_sso_user_id = factory.Sequence(
        lambda n: f"test.user.{n}@test.gov.uk"
    )
    legacy_sso_user_id = factory.Sequence(lambda n: f"legacy_sso_{n}")
    username = legacy_sso_user_id = factory.Sequence(
        lambda n: f"test.user.{n}@id.test.gov.uk"
    )
    sso_contact_email = legacy_sso_user_id = factory.Sequence(
        lambda n: f"test.user.{n}@test.gov.uk"
    )
