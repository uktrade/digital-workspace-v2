(function () {
  const template = document.createElement("template");

  template.innerHTML = `
    <style>
      span span {
        background: yellow;
      }
    </style>
    <span></span>
  `;

  class HighlightText extends HTMLElement {
    static get observedAttributes() {
      return ["text", "pattern"];
    }

    constructor() {
      super();

      this.attachShadow({ mode: "open" });
      this.shadowRoot.append(template.content.cloneNode(true));
    }

    connectedCallback() {
      this.span = this.shadowRoot.querySelector("span");
      this.render();
    }

    get text() {
      return this.getAttribute("text") || "";
    }

    set text(value) {
      this.setAttribute("text", value);
    }

    get pattern() {
      return this.getAttribute("pattern") || "";
    }

    set pattern(value) {
      this.setAttribute("pattern", value);
    }

    render() {
      if (!this.span) {
        return;
      }

      const html = this.text.replaceAll(this.pattern, `<span>${this.pattern}</span>`);

      const template = document.createElement("template");
      template.innerHTML = html;

      this.span.innerHTML = "";
      this.span.append(template.content.cloneNode(true));
    }

    attributeChangedCallback(name, oldValue, newValue) {
      console.log(name, oldValue, newValue);
      if (oldValue !== newValue) {
        this.render();
      }
    }
  }

  customElements.define("highlight-text", HighlightText);
})();
