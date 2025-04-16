(function () {
  /**
   *
   * @param {String} html
   * @returns {Node}
   */
  function htmlTemplate(html) {
    const template = document.createElement("template");
    template.innerHTML = html;

    return template.content.cloneNode(true);
  }

  /**
   *
   * @returns {String}
   */
  function getProfileCardUrl() {
    const metaName = "profile-card-url";
    const meta = document.querySelector(`meta[name="${metaName}"]`);

    return meta.content;
  }

  /**
   *
   * @returns {Node}
   */
  async function getProfileCard() {
    const url = getProfileCardUrl();

    const response = await fetch(url, {
      credentials: "include",
      cache: "default",
    });

    if (!response.ok) {
      throw new Error("Error fetching profile card");
    }

    const html = await response.text();

    return htmlTemplate(html);
  }

  /**
   *
   */
  class ProfileCard extends HTMLElement {
    constructor() {
      super();

      const css = `
        <style>
          :host {
            display: inline-block;
            width: 100%;
          }
          a {
            color: inherit;
            text-decoration: none;
          }
          ul {
            padding: 0;
            list-style-type: none;
          }
          .profile-card {
            font-family: "GDS Transport", arial, sans-serif;
            height: 40px;
            display: flex;
            flex-direction: row-reverse;
            gap: 0.5rem;
            align-items: center;
            container-type: inline-block;
          }
          .profile-photo {
            height: 100%;
            object-fit: cover;
            aspect-ratio: 1 / 1;
          }
          .profile-details {
            text-align: right;
          }
          .profile-name {
            text-decoration: underline;
          }
          .profile-completion {
            font-size: 0.875rem;
          }
          .loading .profile-photo {
            background-color: lightgray;
          }
        </style>
        <div class="profile-card loading">
          <div class="profile-photo"></div>
          <div class="profile-details">
            <ul>
              <li class="profile-name"></li>
              <li>Loading...</li>
            </ul>
          </div>
        </div>
      `;

      const cssTemplate = htmlTemplate(css);

      this.attachShadow({ mode: "open" });
      this.shadowRoot.append(cssTemplate);
    }

    async connectedCallback() {
      const profileName = this.getAttribute("profile-name");

      if (profileName) {
        this.find(".profile-name").innerHTML = profileName;
      }

      let html = null;

      try {
        html = await getProfileCard();
      } catch (error) {
        console.log(error);
      }

      if (html) {
        this.shadowRoot.querySelector(".loading").style.display = "none";
        this.shadowRoot.append(html);
      }
    }

    find(selector) {
      return this.shadowRoot.querySelector(selector);
    }
  }

  customElements.define("profile-card", ProfileCard);
})();
