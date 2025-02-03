document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-cta-button').forEach(function (el) {
        const icon = el.querySelector(".cta-icon");
        const iconSVG = icon.querySelector("svg");

        let toggle_class = "";
        if (iconSVG.classList.contains("hover-light")) {
            toggle_class = "light";
        }
        if (iconSVG.classList.contains("hover-dark")) {
            toggle_class = "dark";
        }

        if (toggle_class) {
            el.addEventListener("mouseover", function () {
                iconSVG.classList.add(toggle_class);
            });
            el.addEventListener("mouseout", function () {
                iconSVG.classList.remove(toggle_class);
            });
        }
    });
});