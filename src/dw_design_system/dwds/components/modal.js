function initialiseModal(modalElement) {
    if (modalElement.dataset.dwdsModal) {
        return;
    }
    modalElement.dataset.dwdsModal = true;
    const dialog = modalElement.querySelector("dialog");
    const openElement = modalElement.querySelector("button.dwds-modal-open");
    const closeElements = modalElement.querySelectorAll(
        "button.dwds-modal-close",
    );

    openElement &&
        openElement.addEventListener("click", function () {
            dialog.showModal();
            document.documentElement.classList.add("no-scroll");
        });
    closeElements.forEach((element) => {
        element.addEventListener("click", function () {
            dialog.close();
            document.documentElement.classList.remove("no-scroll");
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
            document.documentElement.classList.remove("no-scroll");
        }
    });
}

export function reInitialiseModals() {
    document.querySelectorAll(".dwds-modal").forEach(function (modalElement) {
        initialiseModal(modalElement);
    });
}

export function initialiseModals() {
    document.addEventListener("DOMContentLoaded", function () {
        reInitialiseModals();
    });
}
