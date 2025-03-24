document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".dwds-modal").forEach(function (modal_element) {
        const dialog = modal_element.querySelector("dialog");
        const openElement = modal_element.querySelector(
            "button.dwds-modal-open",
        );
        const closeElements = modal_element.querySelectorAll(
            "button.dwds-modal-close",
        );

        openElement.addEventListener("click", function () {
            dialog.showModal();
        });
        closeElements.forEach((element) => {
            element.addEventListener("click", function () {
                dialog.close();
            });
        });

        dialog.addEventListener("click", function (event) {
            const rect = dialog.getBoundingClientRect();
            const isInDialog =
                rect.top <= event.clientY &&
                event.clientY <= rect.top + rect.height &&
                rect.left <= event.clientX &&
                event.clientX <= rect.left + rect.width;
            if (!isInDialog) {
                dialog.close();
            }
        });
    });
});
