function toggleById(elem) {
    if (elem.style.display === "none") {
        elem.style.display = "block";
    } else {
        elem.style.display = "none";
    }
}

function toggleAllSections(element){
    const contentElements = document.getElementsByClassName("dwds-accordion-content");
    var displayStyle = "block"
    if (element.innerText === "Hide all sections") {
        displayStyle = "none";
        element.innerText = "Show all sections";
    } else {
        element.innerText = "Hide all sections"
    }
    for (let i = 0; i < contentElements.length; i++) {
        contentElements[i].style.display = displayStyle;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-accordions').forEach(function (accordions) {
        const accordionsInGroup = accordions.querySelectorAll('.dwds-accordion')
        accordionsInGroup.forEach(function (accordion) {
            const accordionHeader = accordion.getElementsByClassName("dwds-accordion-header")[0];
            const accordionContent = accordion.getElementsByClassName("dwds-accordion-content")[0];
            accordionHeader.addEventListener("click", function (e) {
                toggleById(accordionContent);
            });
        });

        const accordionToggleAll = accordions.getElementsByClassName("dwds-accordion-show-all-text")[0];
        accordionToggleAll.addEventListener("click", function (e) {
                toggleAllSections(accordionToggleAll);
        });
    });
});