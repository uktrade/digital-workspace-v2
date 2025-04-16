function isExternalLink(url) {
    const schemas = ["http:", "https:"];
    if (!schemas.some(schema => url.protocol == schema)) {
        return false;
    }
    return new URL(document.baseURI).origin !== url.origin;
}

function addExternalLinkText(anchorElement, anchorLink, settings) {

    if (anchorElement.dataset.dwdsExternalLink) {
        return;
    }
    anchorElement.dataset.dwdsExternalLink = true;

    const anchorDomain = anchorLink.hostname;
    if (settings.exclude_domains.includes(anchorDomain)) {
        return;
    }
    const anchorWrapper = document.createElement("span");
    anchorElement.parentNode.replaceChild(anchorWrapper, anchorElement);
    anchorWrapper.appendChild(anchorElement);

    const anchorText = settings.domain_mapping[anchorDomain] || "external link";
    const externalText = document.createElement("span");
    externalText.classList.add("dwds-link-external");
    externalText.dataset.externalLinkText = " [" + anchorText + "]";

    anchorElement.insertAdjacentElement("afterend", externalText);
}

function addExternalTextToAnchor(anchorElement, settings) {
    const anchorLink = new URL(anchorElement.getAttribute("href"), document.baseURI);

    if (!isExternalLink(anchorLink)) {
        return;
    }

    addExternalLinkText(anchorElement, anchorLink, settings);
}


export function reInitialiseLinks() {
    const settings = JSON.parse(document.getElementById('external-links-settings').textContent);
    if (!settings.enabled) {
        return;
    }
    // Add external link text to all existing anchor elements
    document.querySelectorAll('a').forEach(function (anchorElement) {
        addExternalTextToAnchor(anchorElement, settings);
    });
}

export function initialiseLinks() {
    document.addEventListener('DOMContentLoaded', function () {
        reInitialiseLinks();
    });
}


