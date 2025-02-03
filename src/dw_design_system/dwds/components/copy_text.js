document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-copy-text').forEach(function (copy_text_element) {
        const copyButton = copy_text_element.querySelector("button");

        copyButton.addEventListener("click", function () {
            const textSpan = copyButton.getElementsByTagName("span")[0];
            const text = "Copy";

            navigator.clipboard.writeText(text);
            textSpan.innerHTML = "Copied";
            setTimeout(() => (
                textSpan.innerHTML = text
            ), 2000);
        });
    });
});