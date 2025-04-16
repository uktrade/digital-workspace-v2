# Reactions

![Page reactions](../../../assets/features/page-reactions.png){ loading=lazy }
![Comment reactions](../../../assets/features/comment-reactions.png){ loading=lazy }

## What reaction types are enabled?

Currently, we have the following reaction types developed:

* Celebrate
* Like
* Love
* Dislike
* Unhappy

To manage which reactions are currently available on the website, we have an environment setting called `INACTIVE_REACTION_TYPES`.
Setting `INACTIVE_REACTION_TYPES` to a comma separated list of the reaction types you wish to disable will make them no longer visible on the frontend.
It will NOT remove reactions for that type from the database.
