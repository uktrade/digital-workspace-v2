"use strict";

(function () {
  const TEAM_SELECT_CACHE = {
    teamSelectData: null,
  };

  const TEAM_SELECT_ACTION = {
    SELECT_TEAM: "select-team",
    EXPAND_TEAM: "expand-team",
  };

  const rightTriangleIcon = template(`
    <svg width="16" height="16" viewBox="0 0 64 64">
      <polygon points="0 0, 64 32, 0 64" fill="#1d70b8" />
    </svg>
  `);

  const squareIcon = template(`
    <svg width="16" height="16" viewBox="0 0 64 64">
      <polygon points="0 0, 64 64, 0 64, 64 0" fill="#ffffff" />
    </svg>
  `);

  /**
   * # Team select web component
   *
   * ## Attributes
   *
   * ### `name`
   * Name given to the input which will be submitted.
   *
   * ### `url`
   * URL for the team select data. See the section "Team select data format" for
   * the specification.
   *
   * ### `current-team-id`
   * ID of the current team.
   *
   * ### `selected-team-id`
   * ID of the currently selected team.
   *
   * ### `editing`
   * Whether the component is in edit mode.
   * Valid values are "true" and "false". Default is "false".
   *
   * ### `disable-current-team`
   * Whether the current team and it's children will be disabled.
   *
   * This is useful to disallow selecting the current team or a child of it when
   * managing a team, as this would create a cyclic relationship.
   *
   * Valid values are "true" and "false". Default is "false".
   *
   * ## Team select data format
   * ```json
   * [
   *     {
   *         "team_id": number,
   *         "team_name": string,
   *         "parent_id": ?number,
   *         "parent_name": ?string,
   *     }
   * ]
   * ```
   *
   * ## Styles
   * The styling can be found in
   * `assets/stylesheets/components/_peoplefinder.scss`.
   *
   * ## Notes
   * - does not use a shadow dom
   *   - so we can use GDS styles
   *   - and the input can be submitted
   */
  class TeamSelect extends HTMLElement {
    constructor() {
      super();

      // state
      this.name = null;
      this.teams = [];
      this.rootTeam = null;
      this.selectedTeam = null;
      this.currentTeam = null;
      this.disableCurrentTeam = false;

      // binding methods
      this.getTeamSelectData = this.getTeamSelectData.bind(this);
      this.updateTeams = this.updateTeams.bind(this);
      this.renderTeam = this.renderTeam.bind(this);
      this.handleChangeTeam = this.handleChangeTeam.bind(this);
      this.handleSelectTeam = this.handleSelectTeam.bind(this);
      this.handleTeamSearch = this.handleTeamSearch.bind(this);
    }

    connectedCallback() {
      this.name = this.getAttribute("name");
      const url = this.getAttribute("url");
      this.disableCurrentTeam =
        (this.getAttribute("disable-current-team") || "false") === "true" ? true : false;

      this.innerHTML = `
      <div class="team-select">
          <div class="govuk-body" id="team-name"></div>
          <input
            class="govuk-button govuk-button--secondary"
            type="button"
            id="change-team"
            value="Change team"
          >
          <div id="team-selector">
            <div class="govuk-form-group">
              <label class="govuk-label">Search for a team</label>
              <input
                class="govuk-input"
                type="search"
                id="team-search"
                placeholder="New Corporate Tools"
              >
              <div class="team-select__teams" id="teams"></div>
            </div>
          </div>
        </div>
      `;

      this.teamNameEl = this.querySelector("#team-name");
      this.changeTeamEl = this.querySelector("#change-team");
      this.teamSelectorEl = this.querySelector("#team-selector");
      this.teamSearchEl = this.querySelector("#team-search");
      this.teamsEl = this.querySelector("#teams");

      if (!this.editing) {
        this.teamSelectorEl.style.display = "none";
      } else {
        this.changeTeamEl.style.display = "none";
      }

      this.getTeamSelectData(url).then((data) => {
        this.teams = data;
        this.rootTeam = this.teams.find((team) => !team.parent_id);
        this.selectedTeam = this.teams.find((team) => team.team_id === this.selectedTeamId);

        if (this.currentTeamId) {
          this.currentTeam = this.teams.find((team) => team.team_id === this.currentTeamId);
        }

        if (!this.selectedTeam) {
          this.selectedTeamId = this.rootTeam.team_id;
          this.selectedTeam = this.rootTeam;
        }

        this.teamNameEl.innerHTML = this.selectedTeam.team_name;

        this.updateTeams();

        for (const team of this.parentsOfTeam(this.selectedTeam)) {
          this.toggleTeam(team.team_id, true);
        }
      });

      this.teamsEl.addEventListener("click", this.handleSelectTeam);
      this.changeTeamEl.addEventListener("click", this.handleChangeTeam);
      this.teamSearchEl.addEventListener("input", debounce(this.handleTeamSearch, 300));
    }

    getTeamSelectData(url) {
      // To avoid lots of repeated calls to the endpoint, we store the results
      // in a cache. This doesn't stop multiple calls at page load if you have
      // multiple roles as they will all trigger before the cache is populated.
      // TODO: Load team select data once on page load.
      if (TEAM_SELECT_CACHE.teamSelectData) {
        return new Promise((resolve, reject) => resolve(TEAM_SELECT_CACHE.teamSelectData));
      }

      return fetch(url)
        .then((response) => response.json())
        .then((teamSelectData) => {
          TEAM_SELECT_CACHE.teamSelectData = teamSelectData;

          return teamSelectData;
        });
    }

    updateTeams() {
      let stack = [this.rootTeam];
      let tree = new Map();

      const rootUl = document.createElement("ul");
      rootUl.classList.add("govuk-radios", "govuk-radios--small");
      rootUl.dataset.module = "govuk-radios";

      tree.set(null, rootUl);

      while (stack.length) {
        const team = stack.pop();
        const children = this.immediateChildrenOfTeam(team);
        stack = stack.concat(children);

        const parentUl = tree.get(team.parent_id);

        const li = this.renderTeam(team, children);
        parentUl.append(li);

        if (children.length) {
          const ul = document.createElement("ul");
          ul.dataset.teamId = team.team_id;
          li.append(ul);
          tree.set(team.team_id, ul);
        }
      }

      this.teamsEl.innerHTML = "";
      this.teamsEl.append(rootUl);
    }

    renderTeam(team, children) {
      const isCurrentTeam = this.currentTeam && team.team_id === this.currentTeam.team_id;
      const isSelectedTeam = team.team_id === this.selectedTeam.team_id;

      const li = document.createElement("li");
      li.dataset.teamId = team.team_id;

      const input_wrapper = document.createElement("div");
      input_wrapper.classList.add("team-select__teams__team");
      const toggle = document.createElement("span");
      const radio_item = document.createElement("div");
      radio_item.classList.add("govuk-radios__item");

      if (children.length) {
        toggle.dataset.action = TEAM_SELECT_ACTION.EXPAND_TEAM;
        toggle.dataset.teamId = team.team_id;
        toggle.append(rightTriangleIcon());
      } else {
        toggle.append(squareIcon());
      }

      input_wrapper.append(toggle);

      const label = document.createElement("label");
      label.classList.add("govuk-label", "govuk-radios__label");
      label.dataset.action = TEAM_SELECT_ACTION.SELECT_TEAM;
      label.dataset.teamId = team.team_id;
      label.for = team.team_id;

      const input = document.createElement("input");
      input.classList.add("govuk-radios__input");
      input.dataset.action = TEAM_SELECT_ACTION.SELECT_TEAM;
      input.dataset.teamId = team.team_id;
      input.type = "radio";
      input.name = this.name;
      input.value = team.team_id;
      input.id = team.team_id;

      if (isSelectedTeam) {
        input.checked = true;
      }

      label.append(team.team_name);

      radio_item.append(input);
      radio_item.append(label);

      input_wrapper.append(radio_item);
      li.append(input_wrapper);

      return li;
    }

    handleChangeTeam(e) {
      this.changeTeamEl.style.display = "none";
      this.teamSelectorEl.style.display = "block";
    }

    handleSelectTeam(e) {
      const el = e.target;

      switch (el.dataset.action) {
        case TEAM_SELECT_ACTION.SELECT_TEAM:
          this.selectedTeamId = parseInt(el.dataset.teamId);
          this.selectedTeam = this.teams.find((team) => team.team_id === this.selectedTeamId);
          this.teamNameEl.innerHTML = this.selectedTeam.team_name;
          break;
        case TEAM_SELECT_ACTION.EXPAND_TEAM:
          this.toggleTeam(el.dataset.teamId);
        default:
          break;
      }
    }

    handleTeamSearch(e) {
      e.preventDefault();

      if (!this.teamSearchEl.value) {
        this.teamsEl.classList.remove("filtered");
        return;
      }

      const searchTerm = this.teamSearchEl.value;
      const searchRegex = new RegExp(`${searchTerm}.*`, "i");
      const matchingTeams = this.teams.filter((team) => searchRegex.test(team.team_name));

      this.teamsEl.classList.add("filtered");

      for (const el of this.querySelectorAll("[data-match]")) {
        el.removeAttribute("data-match");
      }

      for (const team of matchingTeams) {
        this.querySelector(`li[data-team-id="${team.team_id}"]`).dataset.match = "";

        for (const parentTeam of this.parentsOfTeam(team)) {
          this.querySelector(`li[data-team-id="${parentTeam.team_id}"]`).dataset.match = "";
          this.querySelector(`ul[data-team-id="${parentTeam.team_id}"]`).dataset.match = "";

          this.toggleTeam(parentTeam.team_id, true);
        }
      }
    }

    get currentTeamId() {
      return parseInt(this.getAttribute("current-team-id"));
    }

    set currentTeamId(team_id) {
      this.setAttribute("current-team-id", team_id);
    }

    get selectedTeamId() {
      return parseInt(this.getAttribute("selected-team-id"));
    }

    set selectedTeamId(team_id) {
      this.setAttribute("selected-team-id", team_id);
    }

    get editing() {
      return (this.getAttribute("editing") || "false") === "true" ? true : false;
    }

    set editing(flag) {
      this.setAttribute("editing", flag ? "true" : "false");
    }

    toggleTeam(teamId, open) {
      const li = this.querySelector(`li[data-team-id="${teamId}"]`);
      const ul = this.querySelector(`ul[data-team-id="${teamId}"]`);

      if (open === undefined) {
        open = !ul.hasAttribute("data-open");
      }

      if (open) {
        li.setAttribute("data-open", "");
        ul.setAttribute("data-open", "");
      } else {
        li.removeAttribute("data-open");
        ul.removeAttribute("data-open");
      }
    }

    parentsOfTeam(childTeam) {
      const parents = [];
      let parentId = childTeam.parent_id;

      while (parentId) {
        const parent = this.teams.find((team) => team.team_id === parentId);
        parents.push(parent);
        parentId = parent.parent_id;
      }

      return parents;
    }

    immediateChildrenOfTeam(parentTeam) {
      return this.teams.filter((team) => team.parent_id === parentTeam.team_id);
    }
  }

  function debounce(func, wait) {
    let timeout;

    return (...args) => {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };

      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function template(html) {
    const templateEl = document.createElement("template");
    templateEl.innerHTML = html;

    return () => templateEl.content.cloneNode(true);
  }

  customElements.define("team-select", TeamSelect);
})();
