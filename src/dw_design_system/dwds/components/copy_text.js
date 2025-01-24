document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-copy-text').forEach(function (copy_text_elem) {
        const inputField = copy_text_elem.querySelector(".copy-text-input");
        const copyButton = copy_text_elem.querySelector(".copy-text-button");

        copyButton.addEventListener("click", function () {
            const text = inputField.value;
            
            navigator.clipboard.writeText(text);
            inputField.value = "Copied to clipboard";
            // TODO: Change the copy icon on click?
            
            setTimeout(() => (
                inputField.value = text
            ), 2000);
        });
    });
});