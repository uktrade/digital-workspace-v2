"use strict";
/**
 * - `data-formset`
 *   - A formset is made up of many forms `data-formset-form`
 *     - A form has a button to delete the form `data-formset-delete`
 *   - A formset has a button to add a new form `data-formset-add`
 *     - The formset add value is a url to request a new blank form to add to
 *       the formset
 */

function initialiseForm(form) {
    let formsetDelete = form.querySelector("[data-formset-delete]");
    let formsetRemove = form.querySelector("[data-formset-remove]");
    formsetRemove.addEventListener("click", (event) => {
        // Prevent form submission
        event.preventDefault();
        // Hide this form from the user
        form.hidden = true;
        // Set the delete input to true
        formsetDelete.value = true;
    });
}

function initialiseFormset(formset) {
    let formsetPrefix = formset.dataset.formset;
    let formsetTotalForms = formset.querySelector(`[name="${formsetPrefix}-TOTAL_FORMS"]`);
    let formsetForms = formset.querySelectorAll("[data-formset-form]");
    formsetForms.forEach((formsetForm) => {
        initialiseForm(formsetForm);
    });

    const formsetAdd = formset.querySelector("[data-formset-add]");
    formsetAdd.addEventListener("click", (event) => {
        // Prevent form submission
        event.preventDefault();
        // Copy the last form
        let lastForm = formset.querySelector("[data-formset-form]:last-of-type");
        let formNumber = -1;
        if (lastForm) {
            formNumber = parseInt(lastForm.querySelector("[name]").name.replace(`${formsetPrefix}-`, "").split("-")[0]);
        }
        // Work out the form number (get it form the lastForm input names name="PREFIX-N-FIELD_NAME")
        // Increment the form number
        let newFormNumber = formNumber + 1;
        // Request a new blank form to insert
        let blankFormsetUrl = formsetAdd.dataset.formsetAdd + "&new_form_number=" + newFormNumber
        fetch(blankFormsetUrl)
            .then((response) => response.text())
            .then((html) => {
                // Success!
                let newForm = document.createElement("div");
                newForm.innerHTML = html;
                // Insert the new form
                formset.insertBefore(newForm, formsetAdd);
                formsetTotalForms.value = newFormNumber + 1;
                // Initialise the new formset
                initialiseForm(newForm);
            })
            .catch((error) => {
                // Error!
                console.error(error);
            }
        );
    });
}


function initialiseFormsets() {
    let formsets = document.querySelectorAll("[data-formset]");
    formsets.forEach((formset) => {
        initialiseFormset(formset);
    });
}

// Run this code when the page is loaded
document.addEventListener("DOMContentLoaded", initialiseFormsets);
