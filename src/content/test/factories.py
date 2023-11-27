import factory
import wagtail_factories

from content.models import ContentPage
from peoplefinder.test.factories import PersonFactory


class ContentPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = ContentPage


class ContentOwnerFactoryMixin:
    content_owner = factory.SubFactory(PersonFactory)
    content_contact_email = factory.Faker("email")
