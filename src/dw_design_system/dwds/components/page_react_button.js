class PageReactButton extends HTMLElement {
    constructor() {
        super();
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

        this.iconEl = this.querySelector("svg");

        this.render();

        document.addEventListener("reactions:updated", (e) => {
            const reactions = e.detail.reactions;
            this.selected = e.detail.user_reaction === this.type;

            if (this.type in reactions) {
                this.count = reactions[this.type];
            }

            this.render();
        })
    }

    handleClick = async (e) => {
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
        const wrapper = document.createElement("div");
        wrapper.classList.add("content-cluster", "small");

        const button = document.createElement("button");
        button.addEventListener("click", this.handleClick);

        button.classList.add("dwds-button", "dwds-button--clear-icon", "content-with-icon", "no-gap");
        button.setAttribute("title", this.title);
        button.appendChild(this.iconEl);

        wrapper.appendChild(button);
        wrapper.appendChild(document.createTextNode(this.count));
        this.appendChild(wrapper);

        if (this.selected) {
            this.iconEl.classList.add("dark");
        } else {
            this.iconEl.classList.remove("dark");
        }
    }
}

customElements.define("page-react-button", PageReactButton);
