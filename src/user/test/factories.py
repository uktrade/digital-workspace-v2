import uuid
import factory

from user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = "Test"
    last_name = factory.Sequence(lambda n: f"User{n + 1}")
    email = factory.Sequence(lambda n: f"test.user{n + 1}@test.com")
    legacy_sso_user_id = factory.LazyAttribute(lambda _: uuid.uuid4())
    username = factory.Sequence(lambda n: f"test.user{n + 1}@id.test.gov.uk")
    sso_contact_email = factory.Sequence(lambda n: f"test.user{n + 1}@test.com")
