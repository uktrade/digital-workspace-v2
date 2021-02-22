import uuid

import factory

from user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = "Jane"
    last_name = "Smith"
    email = "jane.smith@test.com"
    username = uuid.uuid4()
