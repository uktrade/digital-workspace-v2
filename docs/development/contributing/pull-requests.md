# Pull requests

## Naming

Pull requests should be named using the following format:
`<Jira issue number> <Short description of change>`

For example:
`DWPF-123 Update README.md`

## Reviewing

Pull requests have to be reviewed before they can be merged into `main`. The code should be reviewed by at least one other developer. To help the reviewer, include anything that might be helpful on the PR, things like screenshots of the changes and links to the dev environment.

Make sure you don't include personal/sensitive information in the screenshots.

## Merging

PRs should only be merged once their contents can be considered "production ready". This means that the PR has been reviewed (as stated above) and that the code has been deployed to the dev environment and tested.

Pull requests should be merged using the "Squash and merge" option. This will squash all commits into a single commit and will automatically close the PR. The commit message should contain the Jira issue number if it came from a Jira issue, a short description of the change and finally the PR number. For example:
`DWPF-123 Update README.md (#45)`

Once the PR has been merged, the branch should be deleted.

Code deployed to `main` will be automatically deployed to the staging environment.
