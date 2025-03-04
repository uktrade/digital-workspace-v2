document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-modal').forEach(function (modal_element) {
        const dialog = modal_element.querySelector("dialog");
        const openElement = modal_element.querySelector("button.dwds-modal-open");
        const closeElement = modal_element.querySelector("button.dwds-modal-close");

        openElement.addEventListener("click", function () {
            dialog.showModal();
            document.documentElement.classList.add("no-scroll")
        });
        closeElement.addEventListener("click", function () {
            dialog.close();
            document.documentElement.classList.remove("no-scroll")
        });
        dialog.addEventListener('click', function (event) {
            const rect = dialog.getBoundingClientRect();
            const isInDialog = (
                rect.top <= event.clientY
                && event.clientY <= rect.top + rect.height
                && rect.left <= event.clientX
                && event.clientX <= rect.left + rect.width
            );
            if (!isInDialog) {
                dialog.close();
            }
        });
    });
});