document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-toggle-visibility').forEach(function (toggle_element) {
        // Get data-target-identifier value
        const targetIdentifier = toggle_element.getAttribute("data-target-identifier");
        const targetState = toggle_element.getAttribute("data-target-state");
        const targetElement = document.getElementById(targetIdentifier);

        if (targetState === "hidden") {
            targetElement.style.display = "none";
        } else {
            targetElement.style.display = "block";
        }

        toggle_element.addEventListener("click", function (e) {
            // Check if targetElement is visible
            if (targetElement.style.display === "none" || targetElement.style.display === "") {
                targetElement.style.display = "block";
            } else {
                targetElement.style.display = "none";
            }
        });
    });
});