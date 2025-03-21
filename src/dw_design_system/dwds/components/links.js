export class DWDSLinks {
    constructor() {
    }

    initAll() {
        const localDomains = [
        ];

        const domainMapping = {
        }

        document.querySelectorAll('a').forEach(function (anchor_element) {
            const anchor_link = anchor_element.getAttribute("href");
            // Check if the link starts with http or https
            if (!anchor_link.startsWith("http://") && !anchor_link.startsWith("https://")) {
                return;
            }

            let anchor_domain = anchor_link.split("/")[2];
            if (anchor_domain === null) {
                anchor_domain = "";
            }

            anchor_element.classList.add("dwds-link-external");

            if (!localDomains.includes(anchor_domain)) {
                const after_element = document.createElement("div");
                after_element.classList.add("external-link-text");

                if (domainMapping[anchor_domain]) {
                    anchor_domain = domainMapping[anchor_domain];
                }

                after_element.innerText = "[" + anchor_domain + "]";

                anchor_element.appendChild(after_element);
            }

        });
    }
}

// FIX AFTER REFACTORING
new DWDSLinks().initAll();
