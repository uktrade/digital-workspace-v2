window.addEventListener('DOMContentLoaded', (event) => {
    // Get the event type drop down
    const event_type_field = document.getElementById("id_event_type")

    if (!event_type_field) {
        return
    }

    // Get the in_person wrapper
    const in_person_section = document.getElementById("panel-child-content-in_person_details-section")
    // Get the online wrapper
    const online_section = document.getElementById("panel-child-content-online_details-section")

    if (!in_person_section || !online_section) {
        return
    }

    function event_type_section_toggle(value) {
        switch (value) {
            case "in_person":
                // If the event type is in person, show the in person wrapper
                in_person_section.style.display = "block"
                online_section.style.display = "none"
                break;
            case "online":
                // If the event type is online, show the online wrapper
                in_person_section.style.display = "none"
                online_section.style.display = "block"
                break;
            default:
                // If the event type is hybrid (not in_person or online), show both
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
