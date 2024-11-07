function taggleById(elem) {
    if (elem.style.display === "none") {
        elem.style.display = "block";
    } else {
        elem.style.display = "none";
    }
}

function taggleAllSections(elements) {
    alert(document.getElementById("accordion-header-1").innerText);
    if (document.getElementById("all").innerText === "Hide all sections") {
        for (let i = 1; i <= elements; i++) {
            document.getElementById(i).style.display = "none";
        }
        document.getElementById("all").innerText = "Show all sections"
    } else {
        for (let i = 1; i <= elements; i++) {
            document.getElementById(i).style.display = "block";
        }
        document.getElementById("all").innerText = "Hide all sections";
    }
}


document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-accordions').forEach(function (accordions) {
        const accordionsInGroup = accordions.querySelectorAll('.dwds-accordion')

        accordionsInGroup.forEach(function (accordion) {
            const accordionHeader = accordion.getElementsByClassName("dwds-accordion-header")[0];
            const accordionContent = accordion.getElementsByClassName("dwds-accordion-content")[0];
            console.log(accordionHeader);
            console.log(accordionContent);
            // For each accordion add a click handler to toggle the accordion content visibility
            // Click handler calls `taggleById` passing in the accordionContent element
            // See: https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#the_value_of_this_within_the_handler
        });

        // Add a click handler to the accordion header that toggles the visibility of all of the accordion contents
        // Click handler calls `taggleAllSections` passing in each accordion element
        const accordionsToggleAll = accordion.getElementsByClassName("dwds-accordion-show-all-text")[0];
        console.log(accordionsInGroup);
    });
});