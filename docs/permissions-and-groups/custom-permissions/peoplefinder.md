# `peoplefinder`

Here we describe the different permissions in the `peoplefinder` app.

## AuditLog

### Django permissions

- `peoplefinder.view_auditlog`: Can view the audit logs for **Team** and **Person** objects.

## Person

### Django permissions

- `peoplefinder.change_person`: Can change objects of type **Person**
- `peoplefinder.delete_person`: Can delete objects of type **Person**

### Can view inactive profiles

`peoplefinder.can_view_inactive_profiles`

Can view objects of **Person** that are marked as inactive.

## Team

### Django permissions

- `peoplefinder.add_team`: Can add objects of type **Team**
- `peoplefinder.change_team`: Can change objects of type **Team**
- `peoplefinder.delete_team`: Can delete objects of type **Team**
