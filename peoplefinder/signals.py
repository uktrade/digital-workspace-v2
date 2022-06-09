from django.db.models.signals import post_save
from django.dispatch import receiver

from peoplefinder.models import Person
from peoplefinder.tasks import jml_person_update


@receiver(post_save, sender=Person, dispatch_uid="update_person")
def person_updated(sender, instance, **kwargs):
    print("SIGNAL CALLED", flush=True)
    jml_person_update.delay(instance.id)
