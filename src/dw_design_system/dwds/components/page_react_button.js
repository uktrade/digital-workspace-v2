class PageReactButton extends HTMLElement {
    constructor() {
        super();

        this.handleClick = this.handleClick.bind(this);
    }

    get count() {
        return parseInt(this.getAttribute("count"));
    }

    set count(value) {
        this.setAttribute("count", value);
    }

    get selected() {
        return this.getAttribute("selected") === "true";
    }

    set selected(value) {
        this.setAttribute("selected", value);
    }

    connectedCallback() {
        this.title = this.getAttribute("title");
        this.type = this.getAttribute("type");
        this.postUrl = this.getAttribute("post-url");
        this.csrfToken = this.getAttribute("csrf-token");

        this.iconEl = this.getElementsByTagName("svg")[0];

        this.render();
        this.addEventListener("click", this.handleClick);

        document.addEventListener("reactions:updated", (e) => {
            const reactions = e.detail.reactions;
            this.selected = e.detail.user_reaction === this.type;

            if (this.type in reactions) {
                this.count = reactions[this.type];
            }

            this.render();
        })
    }

    async handleClick(e) {
        // NOTE: This is where you would add an optimistic update.

        const formData = new FormData();
        formData.append("reaction_type", this.type);
        formData.append("is_selected", this.selected);

        fetch(this.postUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
            },
            body: formData,
        }).then((response) => {
            if (!response.ok) {
                throw new Error('Failed to react to this page.');
            }
            return response.json();
        }).then((data) => {
            this.dispatchEvent(new CustomEvent("reactions:updated", { bubbles: true, detail: data }));
        });
    }

    render() {
        this.innerHTML = "";
        const button = document.createElement("button");
        button.classList.add("dwds-button", "dwds-button--clear-icon", "content-with-icon", "small-gap");
        button.setAttribute("title", this.title);
        button.appendChild(this.iconEl);
        button.appendChild(document.createTextNode(this.count));

        this.appendChild(button);

        const icon = this.querySelector("svg");
        if (this.selected) {
            icon.classList.add("dark");
            icon.classList.add("hover-light");
            icon.classList.remove("hover-dark");
        } else {
            icon.classList.remove("dark");
            icon.classList.remove("hover-light");
            icon.classList.add("hover-dark");
        }
    }
}

customElements.define("page-react-button", PageReactButton);
