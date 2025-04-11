# Comments

![Page comments](../../../assets/features/page-comments.png){ loading=lazy }

## Comment deletion

Comments are soft deleted using the `is_visible` field. If the user deletes a comment on the frontend, we simply set this field to `False`.
This is so that we retain the data in case it is needed at some point in the future.

## Comment edits

Comments can be edited, but we use [Django Simple History](https://django-simple-history.readthedocs.io/) to track changes to the model, this means that comments store the history of changes that have been made to them.
