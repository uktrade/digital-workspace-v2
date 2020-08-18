from content.models import Theme


def create_theme(theme):
    Theme.objects.get_or_create(
        theme=theme["title"],
        summary=theme["excerpt"]
    )
