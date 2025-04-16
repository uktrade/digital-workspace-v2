function showSection(accordion) {
    const [content, text, sectionChevron] = getCommonElements(accordion);
    content.style.display = "block";
    text.innerText = "Hide";
    sectionChevron.classList.add("section-chevron-up");
}

function hideSection(accordion) {
    const [content, text, sectionChevron] = getCommonElements(accordion);
    content.style.display = "none";
    text.innerText = "Show";
    sectionChevron.classList.remove("section-chevron-up");
}

function getCommonElements(accordion) {
    const content = accordion.getElementsByClassName("section-content")[0];
    const text = accordion.getElementsByClassName("section-text")[0];
    const sectionChevron = accordion.getElementsByClassName("section-chevron")[0];
    return [content, text, sectionChevron];
}

function toggleSpecificSection(accordion) {
    const sectionText = accordion.getElementsByClassName("section-text")[0];
    if (sectionText.innerText === "Show") {
        showSection(accordion);
    } else {
        hideSection(accordion);
    }
}

function toggleAll(accordions, accordionsInGroup) {
    const allText = accordions.getElementsByClassName("show-all-text")[0];
    const allChevron = accordions.querySelector(".show-all-chevron");
    if (allText.innerText === "Hide all sections") {
        accordionsInGroup.forEach(function (accordion) {
            hideSection(accordion);
        });
        allText.innerText = "Show all sections";
        allChevron.classList.remove("show-all-chevron-up");
    } else {
        accordionsInGroup.forEach(function (accordion) {
            showSection(accordion);
        });
        allText.innerText = "Hide all sections";
        allChevron.classList.add("show-all-chevron-up");
    }
}

document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('.dwds-accordions').forEach(function (accordions) {

        const accordionsInGroup = accordions.querySelectorAll('.dwds-accordion-section');
        accordionsInGroup.forEach(function (accordion) {
            const accordionHeader = accordion.getElementsByClassName("section-header")[0];
            accordionHeader.addEventListener("click", function (e) {
                toggleSpecificSection(accordion);
            });
        });

        const allHeader = accordions.getElementsByClassName("show-all-header")[0];
        allHeader.addEventListener("click", function (e) {
            toggleAll(accordions, accordionsInGroup);
        });

    });
});