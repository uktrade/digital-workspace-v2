from django.utils.safestring import mark_safe
from wagtail import hooks


@hooks.register("insert_editor_js")
def editor_js():
    # TODO: Replace this with the actual JavaScript
    return mark_safe(  # noqa: S308
        """
        <script>
            window.addEventListener('DOMContentLoaded', (event) => {
                // Get the event type drop down
                // Get the in_person wrapper
                // Get the online wrapper

                // Add an event listener to the event type drop down
                // If the event type is in person, show the in person wrapper
                // If the event type is online, show the online wrapper
                // If the event type is hybrid, show both
            });
        </script>
        """
    )
