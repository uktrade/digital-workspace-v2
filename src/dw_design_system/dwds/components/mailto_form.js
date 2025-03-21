document.addEventListener('DOMContentLoaded', function () {
    form_elements = document.querySelectorAll('form.mailto-form')
    
    form_elements.forEach(form_element => {
        form_element.addEventListener("submit", function (event) {
            event.preventDefault();
            sendEmail(form_element);
        });
    });

    function sendEmail(form) {
        let to = form.to;
        let cc = form.cc;
        let bcc = form.bcc;
        let subject = form.subject;
        let body = form.body || form.querySelector('[name="body"]');
        body = body.value ? body.value : body.textContent.trim() || "";

        let mailto_url = "mailto:";
        if (to) mailto_url += to.value;

        let params = [];

        if (cc) params.push(`cc=${encodeURIComponent(cc.value)}`);
        if (bcc) params.push(`bcc=${encodeURIComponent(bcc.value)}`);
        if (subject) params.push(`subject=${encodeURIComponent(subject.value)}`);
        if (body) params.push(`body=${encodeURIComponent(removeIndentation(body))}`);

        if (params.length > 0) mailto_url += `?${params.join("&")}`;
        window.location.href = mailto_url;
    }

    function removeIndentation(text) {
        let lines = text.split("\n");
        return lines.map(line => line.trim()).join("\n");
    }
});