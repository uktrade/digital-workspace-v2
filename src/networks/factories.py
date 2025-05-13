import factory

from content.test.factories import ContentOwnerFactoryMixin
from networks.models import Network
from peoplefinder.test.factories import PersonFactory
from working_at_dit.tests.factories import PageWithTopicsFactory


class NetworkFactory(ContentOwnerFactoryMixin, PageWithTopicsFactory):
    class Meta:
        model = Network

    content_owner = factory.SubFactory(PersonFactory)
    content_contact_email = factory.Faker("email")
