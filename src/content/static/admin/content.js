function getParentContentPath(el) {
    if (!el.parentElement) {
        return null;
    }
    const contentPath = el.parentElement.getAttribute("data-contentpath");
    if (contentPath === null) {
        return getParentContentPath(el.parentElement);
    }
    return contentPath;
}

function initialiseRoleSelector(el) {
    if (el.dataset.roleSelector) {
        return;
    }
    // RUN CODE TO ADD EVENT HANDLERS
    el.dataset.roleSelector = true;
}

function initialiseStreamfieldChild(
    streamfieldChild,
    contentPath,
    containerChildIndex,
) {
    const streamfieldInput = streamfieldChild.querySelector(
        `input[name='${contentPath}-${containerChildIndex}-type']`,
    );
    const streamfieldType = streamfieldInput.value;
    console.log(streamfieldType);
    initialiseRoleSelector(streamfieldChild);
}
function initialiseStreamfields() {
    const streamfieldContainers = document.querySelectorAll(
        "[data-streamfield-stream-container]",
    );
    streamfieldContainers.forEach((container) => {
        const contentPath = getParentContentPath(container);
        if (!contentPath) {
            return;
        }

        const streamfieldChildren = container.querySelectorAll(
            "[data-streamfield-child]",
        );
        let containerChildIndex = 0;
        streamfieldChildren.forEach((streamfieldChild) => {
            initialiseStreamfieldChild(
                streamfieldChild,
                contentPath,
                containerChildIndex,
            );
            containerChildIndex++;
        });
    });
}

window.addEventListener("DOMContentLoaded", (event) => {
    initialiseStreamfields();
});
