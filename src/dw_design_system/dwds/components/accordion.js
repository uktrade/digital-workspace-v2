function showSection(accordion) {
    const content = accordion.getElementsByClassName("dwds-accordion-section-content")[0];
    const text = accordion.getElementsByClassName("dwds-accordion-section-toggle-text")[0];
    const sectionChevron = accordion.getElementsByClassName("dwds-accordion-section-chevron")[0];
    content.style.display = "block";
    text.innerText = "Hide";
    sectionChevron.classList.remove("dwds-accordion-nav-chevron-down");
}

function hideSection(accordion) {
    const content = accordion.getElementsByClassName("dwds-accordion-section-content")[0];
    const text = accordion.getElementsByClassName("dwds-accordion-section-toggle-text")[0];
    const sectionChevron = accordion.getElementsByClassName("dwds-accordion-section-chevron")[0];
    content.style.display = "none";
    text.innerText = "Show";
    sectionChevron.classList.add("dwds-accordion-nav-chevron-down");
}

function toggleSpecificSection(element) {
    const accordionContent = element.getElementsByClassName("dwds-accordion-section-content")[0];
    if (accordionContent.style.display === "none") {
        showSection(element);
    } else {
        hideSection(element);
    }
}

function toggleAll(element, allChevron, accordionsInGroup) {
    if (element.innerText === "Hide all sections") {
        accordionsInGroup.forEach(function (accordion) {
            hideSection(accordion);
        });
        element.innerText = "Show all sections";
        allChevron.classList.add("dwds-accordion-show-all-chevron-down");
    } else {
        element.innerText = "Hide all sections";
        accordionsInGroup.forEach(function (accordion) {
            showSection(accordion);
        });
        allChevron.classList.remove("dwds-accordion-show-all-chevron-down");
    }
}

document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('.dwds-accordions').forEach(function (accordions) {

        const accordionsInGroup = accordions.querySelectorAll('.dwds-accordion-section');
        accordionsInGroup.forEach(function (accordion) {
            const accordionHeader = accordion.getElementsByClassName("dwds-accordion-section-header")[0];
            accordionHeader.addEventListener("click", function (e) {
                toggleSpecificSection(accordion);
            });

            const accordionContent = accordion.getElementsByClassName("dwds-accordion-section-content")[0];
            accordionContent.style.display = "none";
            const toggleChevron = accordion.querySelector(".dwds-accordion-section-chevron");
            toggleChevron.classList.add("dwds-accordion-nav-chevron-down");
        });

        const accordionToggleAll = accordions.getElementsByClassName("dwds-accordion-show-all-text")[0];
        const allChevron = accordions.querySelector(".dwds-accordion-show-all-chevron");
        allChevron.classList.add("dwds-accordion-show-all-chevron-down");
        accordionToggleAll.addEventListener("click", function (e) {
            toggleAll(accordionToggleAll, allChevron, accordionsInGroup);
        });
    });
});