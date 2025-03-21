function toggleElement(currentElement, swapElement) {
    if (swapElement.style.display === "none" || swapElement.style.display === "") {
        currentElement.style.display = "none";
        swapElement.style.display = "block";
    } else {
        currentElement.style.display = "block";
        swapElement.style.display = "none";
    }
}