document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-copy-text').forEach(function (copy_text_element) {
        const inputField = copy_text_element.querySelector("input");
        const copyButton = copy_text_element.querySelector("button");

        copyButton.addEventListener("click", function () {
            const text = inputField.value;
            
            navigator.clipboard.writeText(text);
            inputField.value = "Copied to clipboard";
            // TODO: INTR-542 - Change the success icon on click
            
            setTimeout(() => (
                inputField.value = text
            ), 2000);
        });
    });
});