# Releasing

Releases are done using the GitHub releases feature.

- Go to the [releases page](https://github.com/uktrade/digital-workspace-v2/releases) and click the "Draft a new release" button.
- At the top of the page click "Choose a tag" and create a new tag using the following format: `YYYY-MM.N` where `YYYY` is the current year, `MM` is the current month and `N` is the next release number.
  - For example if the date is Sept 2023 and this is the first release of this month the tag would be: `2023-09.1`
- Now, simply press the "Generate release notes" and review the release notes.
  - You can share these notes with the team to ensure that they are happy with the release.
- Finally, press the "Publish release" button. This will trigger a deployment to the production environment.

## Release checklist

When upgrading wagtail, check the:

- front page
  - news showing
- content search
- people finder search
- people finder
  - view profile
  - edit profile
  - view team
  - edit team
- django admin
- wagtail admin
  - home news order
    - drag to sort
  - add a news page
    - upload and add an image
    - publish and view live
    - appears on home page
    - appears on news page
