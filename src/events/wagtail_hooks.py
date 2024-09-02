from django.utils.safestring import mark_safe
from wagtail import hooks


@hooks.register("insert_editor_js")
def editor_js():
    return mark_safe(  # noqa: S308
        """
        <script>
            window.addEventListener('DOMContentLoaded', (event) => {
                // Get the event type drop down
                var event_type_field = document.getElementById("id_event_type")

                if (!event_type_field) {
                    return
                }

                // Get the in_person wrapper
                var in_person_section = document.getElementById("panel-child-content-in_person_details-section")
                // Get the online wrapper
                var online_section = document.getElementById("panel-child-content-online_details-section")

                if (!in_person_section || !online_section) {
                    return
                }

                function event_type_section_toggle (value) {
                    // If the event type is in person, show the in person wrapper
                    if (value == "in_person") {
                        in_person_section.style.display = "block"
                        online_section.style.display = "none"
                    }

                    // If the event type is online, show the online wrapper
                    else if (value == "online") {
                        in_person_section.style.display = "none"
                        online_section.style.display = "block"
                    }

                    // If the event type is hybrid, show both
                    else if (value == "hybrid") {
                        in_person_section.style.display = "block"
                        online_section.style.display = "block"
                    }
                }

                // Call the function to get correct state for the default event type
                event_type_section_toggle(event_type_field.value)

                // Add an event listener to the event type drop down
                event_type_field.addEventListener("change", (event) => {
                    new_value = event.target.value
                    event_type_section_toggle(new_value)
                });
            });
        </script>
        """
    )
