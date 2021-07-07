'use strict';

const TEAM_SELECT_CACHE = {
    teamSelectData: null,
}

const TEAM_SELECT_ACTION = {
    NAVIGATE_TO: 'navigate-to',
    SELECT_TEAM: 'select-team',
};

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
        this.teamHasChildren = this.teamHasChildren.bind(this);
    }

    connectedCallback() {
        this.name = this.getAttribute('name');
        const url = this.getAttribute('url');
        this.disableCurrentTeam = (this.getAttribute('disable-current-team') || 'false') === 'true' ? true : false;

        this.innerHTML = `
            <div class="team-select">
                <div id="current-team">
                    <div class="govuk-body" id="team-name"></div>
                    <input
                        class="govuk-button govuk-button--secondary"
                        type="button"
                        id="change-team"
                        value="Change team"
                    >
                </div>
                <div class="team-select__teams" id="teams"></div>
            </div>
        `;

        this.selectedTeamEl = this.querySelector('#current-team');
        this.changeTeamEl = this.querySelector('#change-team');
        this.teamNameEl = this.querySelector('#team-name');
        this.teamsEl = this.querySelector('#teams');

        if (!this.editing) {
            this.teamsEl.style.display = 'none';
        } else {
            this.selectedTeamEl.style.display = 'none';
        }

        this.getTeamSelectData(url)
            .then(data => {
                this.teams = data;
                this.rootTeam = this.teams.find(team => !team.parent_id);
                this.selectedTeam = this.teams.find(team => team.team_id === this.selectedTeamId);

                if (this.currentTeamId) {
                    this.currentTeam = this.teams.find(team => team.team_id === this.currentTeamId);
                }

                if (!this.selectedTeam) {
                    this.selectedTeamId = this.rootTeam.team_id;
                    this.selectedTeam = this.rootTeam;
                }

                this.teamNameEl.innerHTML = this.selectedTeam.team_name;

                this.updateTeams();
            });

        this.teamsEl.addEventListener('click', this.handleSelectTeam);
        this.changeTeamEl.addEventListener('click', this.handleChangeTeam);
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
            .then(response => response.json())
            .then(teamSelectData => {
                TEAM_SELECT_CACHE.teamSelectData = teamSelectData;

                return teamSelectData;
            })
    }

    updateTeams() {
        const ul = document.createElement('ul');
        ul.classList.add('govuk-list');

        // back link
        if (this.parentOfSelectedTeam) {
            const parentTeamLi = document.createElement('li');
            parentTeamLi.innerHTML = `
                <a
                    class="govuk-link govuk-link--no-visited-state team-select__nav-up"
                    href="#"
                    data-action="${TEAM_SELECT_ACTION.NAVIGATE_TO}"
                    data-team-id="${this.parentOfSelectedTeam.team_id}"
                >${this.parentOfSelectedTeam.team_name}</a>
            `;

            ul.append(parentTeamLi);
        }

        // select current team
        ul.append(this.renderTeam(this.selectedTeam));

        // rest of the teams
        ul.append(...this.immediateChildrenOfSelectedTeam.map(this.renderTeam));

        this.teamsEl.innerHTML = '';
        this.teamsEl.append(ul);
    }

    renderTeam(team) {
        const isCurrentTeam = this.currentTeam && team.team_id === this.currentTeam.team_id;
        const isSelectedTeam = team.team_id === this.selectedTeam.team_id;

        
        const li = document.createElement('li');
        li.classList.add('team');

        if (isCurrentTeam && this.disableCurrentTeam) {
            li.classList.add('team-select__leaf-team', 'team-select__current-team');

            li.innerHTML = `${team.team_name}`;
        } else if (this.teamHasChildren(team) && !isSelectedTeam) {
            li.classList.add('team-select__branch-team');

            li.innerHTML = `
                <a
                    class="govuk-link govuk-link--no-visited-state team-select__nav-down"
                    href="#"
                    data-action="${TEAM_SELECT_ACTION.NAVIGATE_TO}"
                    data-team-id="${team.team_id}"
                >${team.team_name}</a>
            `;
        } else {
            li.classList.add(isSelectedTeam ? 'team-select__selected-team' : 'team-select__leaf-team');

            li.innerHTML = `
                <label>
                    <input
                        type="radio"
                        name="${this.name}"
                        value="${team.team_id}"
                        ${isSelectedTeam ? 'checked' : ''}
                        data-action="${TEAM_SELECT_ACTION.SELECT_TEAM}"
                        data-team-id=${team.team_id}
                    >
                    ${team.team_name}
                </label>
            `;
        }

        return li;
    }

    handleChangeTeam(e) {
        this.selectedTeamEl.style.display = 'none';
        this.teamsEl.style.display = 'block';
    }

    handleSelectTeam(e) {
        const el = e.target;

        switch (el.dataset.action) {
            case TEAM_SELECT_ACTION.NAVIGATE_TO:
                e.preventDefault();

                const newSelectedTeamId = parseInt(el.dataset.teamId);
                this.selectedTeamId = newSelectedTeamId;
                this.selectedTeam = this.teams.find(team => team.team_id === newSelectedTeamId);
                this.updateTeams();

                break;
            case TEAM_SELECT_ACTION.SELECT_TEAM:
                this.selectedTeamId = parseInt(el.dataset.teamId);;

                break;
            default:
                break;
        }
    }

    get parentOfSelectedTeam() {
        if (!this.selectedTeam.parent_id) {
            return null;
        }

        return this.teams.find(team => team.team_id === this.selectedTeam.parent_id);
    }

    get immediateChildrenOfSelectedTeam() {
        return this.teams.filter(team => team.parent_id === this.selectedTeam.team_id);
    }

    get currentTeamId() {
        return parseInt(this.getAttribute('current-team-id'));
    }

    set currentTeamId(team_id) {
        this.setAttribute('current-team-id', team_id);
    }

    get selectedTeamId() {
        return parseInt(this.getAttribute('selected-team-id'));
    }

    set selectedTeamId(team_id) {
        this.setAttribute('selected-team-id', team_id);
    }

    get editing() {
        return (this.getAttribute('editing') || 'false') === 'true' ? true : false;
    }

    set editing(flag) {
        this.setAttribute('editing', flag ? 'true' : 'false');
    }

    teamHasChildren(parentTeam) {
        return this.teams.some(team => team.parent_id === parentTeam.team_id);
    }
}

customElements.define('team-select', TeamSelect);
