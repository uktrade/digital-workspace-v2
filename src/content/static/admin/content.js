const getParentContentPathEl = (el) => {
    /*
    Get the first parent element with a `data-contentpath` attribute
    */
    if (!el.parentElement) {
        return null;
    }
    const contentPath = el.parentElement.getAttribute("data-contentpath");
    if (contentPath === null) {
        return getParentContentPathEl(el.parentElement);
    }
    return el.parentElement;
};

const getParentContentPath = (el) => {
    /*
    Get the first parent element with a `data-contentpath` attribute and return
    the value.
    */
    const contentPathEl = getParentContentPathEl(el);
    if (contentPathEl === null) {
        return null;
    }
    return contentPathEl.getAttribute("data-contentpath");
};

const getStreamfieldChildIndex = (container, contentPath) => {
    /*
    Get's the index by looking for the input with the name `body-N-type` and
    returning `n`.
    */
    const orderInputs = container.querySelectorAll(`input[name$='-type']`);
    let orderInput = null;

    if (orderInputs.length == 1) {
        orderInput = orderInputs[0];
    } else {
        orderInputs.forEach((inputEl) => {
            if (inputEl.getAttribute("name").startsWith(contentPath + "-")) {
                orderInput = inputEl;
                return;
            }
        });
    }
    let orderInputNameSplit = orderInput.getAttribute("name").split("-");
    if (
        orderInputNameSplit[0] == contentPath &&
        orderInputNameSplit[2] == "type"
    ) {
        return orderInputNameSplit[1];
    }
    return null;
};

const hideRoleSelector = (roleSelectorEl) => {
    const parentContentPathEl = getParentContentPathEl(roleSelectorEl);
    parentContentPathEl.style.display = "none";
};

const showRoleSelector = (roleSelectorEl) => {
    const parentContentPathEl = getParentContentPathEl(roleSelectorEl);
    parentContentPathEl.style.display = "block";
};

const setSelectOptions = (selectElement, personInput) => {
    const selectedRole = selectElement.value;
    fetch(`/content/get-person-roles/${personInput.value}/`)
        .then((response) => response.json())
        .then((data) => {
            selectElement.innerHTML = "";
            let optionElement = document.createElement("option");
            optionElement.setAttribute("value", "");

            let optionText = document.createTextNode("Hide role");
            optionElement.appendChild(optionText);

            selectElement.appendChild(optionElement);
            data.person_roles.forEach((option) => {
                let optionElement = document.createElement("option");
                optionElement.setAttribute("value", option.pk);

                let optionText = document.createTextNode(option.label);
                optionElement.appendChild(optionText);

                selectElement.appendChild(optionElement);
            });
        })
        .then(() => {
            const availableOptions = Array.from(selectElement.options).map(
                (option) => option.value,
            );
            if (selectedRole && availableOptions.includes(selectedRole)) {
                selectElement.value = selectedRole;
            } else {
                selectElement.value = "";
            }
        });
};

const initialiseRoleSelector = (
    streamfieldChild,
    streamfieldType,
    contentPath,
    containerChildIndex,
) => {
    if (streamfieldChild.dataset.roleSelector) {
        return;
    }
    streamfieldChild.dataset.roleSelector = true;

    const fieldNameMapping = {
        person_banner: {
            personChooser: "person",
            personRole: "person_role_id",
        },
        quote: {
            personChooser: "source",
            personRole: "source_role_id",
        },
    };

    if (!(streamfieldType in fieldNameMapping)) {
        return;
    }

    const personChooserFieldName =
        fieldNameMapping[streamfieldType]["personChooser"];
    const personRoleFieldName = fieldNameMapping[streamfieldType]["personRole"];

    const personInput = document.querySelector(
        `input[name='${contentPath}-${containerChildIndex}-value-${personChooserFieldName}']`,
    );

    const personRoleSelect = document.querySelector(
        `select[name='${contentPath}-${containerChildIndex}-value-${personRoleFieldName}']`,
    );

    if (!personInput.value) {
        hideRoleSelector(personRoleSelect);
    } else {
        setSelectOptions(personRoleSelect, personInput);
    }

    // When the value of the selected person changes, make a request to get roles using the currently selected person ID
    const observer = new MutationObserver((mutations, observer) => {
        for (const mutation of mutations) {
            if (
                mutation.type === "attributes" &&
                mutation.attributeName === "value"
            ) {
                switch (personInput.value) {
                    case "":
                        hideRoleSelector(personRoleSelect);
                        break;
                    default:
                        setSelectOptions(personRoleSelect, personInput);
                        showRoleSelector(personRoleSelect);
                }
            }
        }
    });
    observer.observe(personInput, { attributes: true });
};

const initialiseStreamfieldChild = (streamfieldChild, contentPath) => {
    const containerChildIndex = getStreamfieldChildIndex(
        streamfieldChild,
        contentPath,
    );
    const streamfieldInput = streamfieldChild.querySelector(
        `input[name='${contentPath}-${containerChildIndex}-type']`,
    );

    const streamfieldType = streamfieldInput.value;
    initialiseRoleSelector(
        streamfieldChild,
        streamfieldType,
        contentPath,
        containerChildIndex,
    );
};

const streamfieldContainerObserver = new MutationObserver(
    (mutations, observer) => {
        for (const mutation of mutations) {
            if (mutation.type === "childList") {
                initialiseStreamfields();
            }
        }
    },
);

const initialiseStreamfields = () => {
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
        streamfieldChildren.forEach((streamfieldChild) => {
            initialiseStreamfieldChild(streamfieldChild, contentPath);
        });

        if (!container.dataset.contentJavascriptInitialised) {
            container.dataset.contentJavascriptInitialised = true;
            streamfieldContainerObserver.observe(container, {
                childList: true,
            });
        }
    });
};

window.addEventListener("DOMContentLoaded", (event) => {
    initialiseStreamfields();
});
