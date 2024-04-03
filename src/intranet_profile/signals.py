from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import IntranetProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_intranet_profile(sender, instance, created, **kwargs):
    if created:
        IntranetProfile.objects.create(user=instance)
