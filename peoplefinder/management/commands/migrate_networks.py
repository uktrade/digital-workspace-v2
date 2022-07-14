from django.core.management.base import BaseCommand

from peoplefinder.models import Network


class Command(BaseCommand):
    help = "Migrate networks"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for network in Network.objects.all():
            self.stdout.write(str(network), ending="")

            if hasattr(network, "newnetwork"):
                self.stdout.write(
                    self.style.SUCCESS(f" has a new network ({network.newnetwork})")
                )
            else:
                self.stdout.write(self.style.WARNING(" has no new network"))

        count_networks = Network.objects.count()
        count_has_new_network = Network.objects.filter(newnetwork__isnull=False).count()
        count_no_new_network = Network.objects.filter(newnetwork__isnull=True).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"There are {count_networks} networks"
                f"\n{count_has_new_network} networks have a new network"
                f"\n{count_no_new_network} networks have no new network"
            )
        )
