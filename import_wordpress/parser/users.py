import uuid

from django.conf import settings
from django.contrib.auth import get_user_model


namespaces = settings.NAMESPACES

UserModel = get_user_model()


# Parse out users
def create_users(root):
    for author in root.find("channel").findall("wp:author", namespaces):
        email = author.find("wp:author_email", namespaces).text
        first_name = author.find("wp:author_first_name", namespaces).text
        last_name = author.find("wp:author_last_name", namespaces).text

        if not first_name:
            first_name = ""

        if not last_name:
            last_name = ""

        user = UserModel(
            username=uuid.uuid4(),
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.save()
