document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-modal').forEach(function (modal_element) {
        const dialog = modal_element.querySelector("dialog");
        const openElement = modal_element.querySelector("button.dwds-modal-open");
        const closeElement = modal_element.querySelector("button.dwds-modal-close");

        openElement.addEventListener("click", function () {
            dialog.showModal();
        });
        closeElement.addEventListener("click", function () {
            dialog.close();
        });
    });
});