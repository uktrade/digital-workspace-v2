import uuid

import factory

from user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = "Jane"
    last_name = "Smith"
    email = "jane.smith@test.com"
    legacy_sso_user_id = uuid.uuid4()
    username = "jane.smith@-1111111@id.test.gov.uk"
    sso_contact_email = "jane.smith@test.com"
