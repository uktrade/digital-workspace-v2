function initialiseModal(modalElement) {
    const dialog = modalElement.querySelector("dialog");
    const openElement = modalElement.querySelector(
        "button.dwds-modal-open",
    );
    const closeElements = modalElement.querySelectorAll(
        "button.dwds-modal-close",
    );

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


document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".dwds-modal").forEach(function (modalElement) {
        initialiseModal(modalElement);
    });

    // // Create a MutationObserver to watch for new anchor elements in the DOM
    // const observer = new MutationObserver(function (mutations) {
    //     mutations.forEach(function (mutation) {
    //         if (mutation.type === 'childList') {
    //             mutation.addedNodes.forEach(function (node) {
    //                 if (node.nodeType === 1 && node.classList.contains('dwds-modal')) {
    //                     initialiseModal(node);
    //                 }
    //             });
    //         }
    //     });
    // });
    // // Observe the document body for changes
    // observer.observe(document.body, {
    //     childList: true,
    //     subtree: true
    // });
});
