function isExternalLink(url) {
    const schemas = ["http:", "https:"];
    if (!schemas.some(schema => url.protocol == schema)) {
        return false;
    }
    return new URL(document.baseURI).origin !== url.origin;
}

function addExternalLinkText(anchorElement, anchorLink, settings) {
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

document.addEventListener('DOMContentLoaded', function () {
    const settings = JSON.parse(document.getElementById('external-links-settings').textContent);
    if (!settings.enabled) {
        return;
    }

    // Add external link text to all existing anchor elements
    document.querySelectorAll('a').forEach(function (anchorElement) {
        addExternalTextToAnchor(anchorElement, settings);
    });

    // Create a MutationObserver to watch for new anchor elements in the DOM
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === 1 && node.tagName === 'A') {
                        addExternalTextToAnchor(node, settings);
                    }
                });
            }
        });
    });
    // Observe the document body for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});