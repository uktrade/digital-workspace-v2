const hideElement = (element) => {
    element.style.display = "none";
};

const showElement = (element) => {
    element.style.display = "block";
};

const setRoleSelectOptions = (selectElement, personInput) => {
    const selectedRole = selectElement.value;
    fetch(`/content/get-user-roles/${personInput.value}/`)
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

const updatePageAuthorVisibility = (
    pageAuthorInput,
    pageAuthorRoleElement,
    pageAuthorRoleSelect,
    pageAuthorShowTeamElement,
) => {
    /* 
    When the value of the selected author changes, 
    show/hide the role and team elements depending on their values
    */
    if (!pageAuthorInput.value) {
        hideElement(pageAuthorRoleElement);
        hideElement(pageAuthorShowTeamElement);
    }
    else {
        setRoleSelectOptions(pageAuthorRoleSelect, pageAuthorInput);
        showElement(pageAuthorRoleElement);
        if (pageAuthorRoleSelect.value) {
            showElement(pageAuthorShowTeamElement);
        }
        else {
            hideElement(pageAuthorShowTeamElement);
        }
    }
};

const initialisePageAuthor = () => {
    const pageAuthorInput = document.querySelector(
        `input[name='page_author']`
    );
    const pageAuthorRoleElement = document.querySelector(
        `section[id='panel-child-publishing-page_author_role-section']`,
    );
    const pageAuthorRoleSelect = document.querySelector(
        `select[name='page_author_role']`,
    );
    const pageAuthorShowTeamElement = document.querySelector(
        `section[id='panel-child-publishing-page_author_show_team-section']`,
    );

    updatePageAuthorVisibility(
        pageAuthorInput,
        pageAuthorRoleElement,
        pageAuthorRoleSelect,
        pageAuthorShowTeamElement,
    );

    /*  
    When the value of the selected person changes, 
    make a request to get roles using the currently selected person ID
    */
    const pageAuthorObserver = new MutationObserver((mutations, observer) => {
        for (const mutation of mutations) {
            if (
                mutation.type === "attributes" &&
                mutation.attributeName === "value"
            ) {
                updatePageAuthorVisibility(
                    pageAuthorInput,
                    pageAuthorRoleElement,
                    pageAuthorRoleSelect,
                    pageAuthorShowTeamElement,
                );
                /* 
                When the value of the selected role changes, 
                show/hide the show team checkbox depending on the value 
                */
                pageAuthorRoleSelect.addEventListener('change', () => {
                    if (!pageAuthorRoleSelect.value) {
                        hideElement(pageAuthorShowTeamElement);
                    } else {
                        showElement(pageAuthorShowTeamElement);
                    }
                });
            }
        }
    });
    pageAuthorObserver.observe(pageAuthorInput, { attributes: true });
};

window.addEventListener("DOMContentLoaded", (event) => {
    initialisePageAuthor();
});