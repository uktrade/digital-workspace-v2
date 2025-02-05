document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-copy-text').forEach(function (copy_text_element) {
        const inputField = copy_text_element.querySelector("input");
        const copyButton = copy_text_element.querySelector("button");

        copyButton.addEventListener("click", function () {
            navigator.clipboard.writeText(inputField.value);

            copyButton.classList.add("copied");
            setTimeout(() => (
                copyButton.classList.remove("copied")
            ), 2000);
        });
    });
});