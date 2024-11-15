function toggleSpecificSection(element, headerElement, chevronElement) {
    if (element.style.display === "none") {
        element.style.display = "block";
        headerElement.innerText = "Hide";
        chevronElement.classList.remove("dwds-accordion-nav-chevron-down");
    } else {
        element.style.display = "none";
        headerElement.innerText = "Show";
        chevronElement.classList.add("dwds-accordion-nav-chevron-down");
    }
}

function toggleAllSections(element) {
    const contentElements = document.getElementsByClassName("dwds-accordion-section-content");
    const textElements = document.querySelectorAll(".dwds-accordion-section-toggle-text")
    var displayStyle = "block";
    const chevronElements = document.querySelectorAll(".dwds-accordion-section-chevron");
    const accordionChevronAll = document.getElementsByClassName("dwds-accordion-show-all-chevron")[0];
    if (element.innerText === "Hide all sections") {
        chevronElements.forEach(function(changeArrow){
            changeArrow.classList.add("dwds-accordion-nav-chevron-down");
        });
        displayStyle = "none";
        textElements.forEach(function(showEl){
            showEl.innerText = "Show";
        });
        accordionChevronAll.classList.add("dwds-accordion-show-all-chevron-down");
        element.innerText = "Show all sections";
    } else {
        accordionChevronAll.classList.remove("dwds-accordion-show-all-chevron-down");
        element.innerText = "Hide all sections";
        textElements.forEach(function(showEl){
            showEl.innerText = "Hide";
        });
        chevronElements.forEach(function(changeArrow){
            changeArrow.classList.remove("dwds-accordion-nav-chevron-down");
        });
    }
    for (let i = 0; i < contentElements.length; i++) {
        contentElements[i].style.display = displayStyle;
    }
}


document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-accordions').forEach(function (accordions) {
        const accordionsInGroup = accordions.querySelectorAll('.dwds-accordion-section')
        accordionsInGroup.forEach(function (accordion) {
            const accordionHeader = accordion.getElementsByClassName("dwds-accordion-section-header")[0];
            const accordionContent = accordion.getElementsByClassName("dwds-accordion-section-content")[0];
            accordionContent.style.display = "none";
            const toggleText = accordion.getElementsByClassName("dwds-accordion-section-toggle-text")[0];
            const toggleChevron = accordion.querySelector(".dwds-accordion-section-chevron");
            toggleChevron.classList.add("dwds-accordion-nav-chevron-down");
            accordionHeader.addEventListener("click", function (e) {
                toggleSpecificSection(accordionContent, toggleText, toggleChevron);
            });
        });
        const accordionToggleAll = accordions.getElementsByClassName("dwds-accordion-show-all-text")[0];
        const accordionChevronAll = document.getElementsByClassName("dwds-accordion-show-all-chevron")[0];
        accordionChevronAll.classList.add("dwds-accordion-show-all-chevron-down");
        accordionToggleAll.addEventListener("click", function (e) {
            toggleAllSections(accordionToggleAll);
        });
    });
});