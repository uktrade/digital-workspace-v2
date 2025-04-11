# People Finder

The DIT's people and team directory. Written as a Django application inside of Digital
Workspace.

## Design decisions

- Make extensive use of many-to-many fields for multiple choice reference data, e.g.
  country.

### Soft Delete

When a profile is deleted by an admin, they are marked as inactive. If the user
connected to the profile attempts to access the system, they will be redirected to a
page explaining they have been deactivated. Inactive profiles will only be visible to
admins and can only be reactivated by admins.

To support this feature in the codebase, the `Person` model and the `TeamMember` model
both have an `active` manager which filters for active people. Both models retain
the unfiltered `objects` manager as their default, so that the system can access
inactive profiles for admins to manage. To make things easier, both models' `objects`
manager have an `active()` queryset method to filter for active profiles. This is useful
when you are performing queries across related managers which use the default `objects`
manager.

Here are some examples:

```python
# All users.
Person.objects.all()

# Active users.
Person.active.all()
Person.objects.active()

# All team members.
TeamMember.objects.all()

# Active team members.
TeamMember.active.all()
TeamMember.objects.active()

# All team members through a related team.
team.members.all()

# Active team members through a related team.
team.members.active()
# https://docs.djangoproject.com/en/4.0/topics/db/queries/#using-a-custom-reverse-manager
team.members(manager="active").all()
```

Please take care to make sure any code you write uses the correct manager, or applies
the appropriate filters for your use case.

## Integrations

- GOV.UK Notify
  - Notify users about changes made to their profile
- Zendesk (via email)
  - Creates a ticket when a person is marked as having left the DIT

## APIs

- Data Workspace
  - API for people data

## Audit log

**Please remember to use the audit log service after you have made model instance
changes that you wish to be tracked!**

After evaluating a number of packages, we decided to write our own audit log system. The
main reason for doing this is because no package would track changes to many-to-many
fields without us having to make changes to how the app is written. Therefore, we
decided it was best to keep the implementation of the app simple and write our own audit
log system.

The audit log system we have written does not make use of django signals. This is
because that approach has difficulties handling many-to-many fields. Instead, we have a
simple and explicit approach where you must call the audit log service after you have
made changes for them to be tracked.

For this approach to work you will need to provide a flat, serialized and denormalized
"view" of the model you wish to be tracked. This allows us to avoid the complexity of
tracking many-to-many fields by denormalizing them. This is often achieved using
`ArrayAgg` which provides an array representation of the many-to-many relationship. For
an example of this in action, please take a look at the `PersonAuditLogSerializer` class
in `peoplefinder/services/person.py`.

One downside to this approach is that if you do not call the audit log service after
making a change, for example modifying a model instance in a shell, then the changes
will not be tracked.

For more information, please read through the docstrings and code in
`peoplefinder/services/audit_log.py` and check out an example of how to use the service
from a view in the `ProfileEditView` class in `peoplefinder/views/profile.py`.
