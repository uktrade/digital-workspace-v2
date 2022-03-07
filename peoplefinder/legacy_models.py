# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.postgres.fields import ArrayField
from django.db import models


class LegacyPeopleFinderModel(models.Model):
    class Meta:
        abstract = True


# class ArInternalMetadata(models.Model):
#     key = models.CharField(primary_key=True, max_length=-1)
#     value = models.CharField(max_length=-1, blank=True, null=True)
#     created_at = models.DateTimeField()
#     updated_at = models.DateTimeField()

#     class Meta:
#         managed = False
#         db_table = 'ar_internal_metadata'


class Groups(LegacyPeopleFinderModel):
    people = models.ManyToManyField(
        "People", through="Memberships", related_name="groups"
    )

    name = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    ancestry = models.TextField(blank=True, null=True)
    ancestry_depth = models.IntegerField()
    acronym = models.TextField(blank=True, null=True)
    members_completion_score = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "groups"


class Memberships(LegacyPeopleFinderModel):
    group = models.ForeignKey("Groups", models.DO_NOTHING, related_name="members")
    person = models.ForeignKey("People", models.DO_NOTHING, related_name="roles")
    role = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    leader = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "memberships"


class People(LegacyPeopleFinderModel):
    given_name = models.TextField(blank=True, null=True)
    surname = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    primary_phone_number = models.TextField(blank=True, null=True)
    secondary_phone_number = models.TextField(blank=True, null=True)
    location_in_building = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    works_monday = models.BooleanField(blank=True, null=True)
    works_tuesday = models.BooleanField(blank=True, null=True)
    works_wednesday = models.BooleanField(blank=True, null=True)
    works_thursday = models.BooleanField(blank=True, null=True)
    works_friday = models.BooleanField(blank=True, null=True)
    slug = models.CharField(unique=True, max_length=255, blank=True, null=True)
    works_saturday = models.BooleanField(blank=True, null=True)
    works_sunday = models.BooleanField(blank=True, null=True)
    login_count = models.IntegerField()
    last_login_at = models.DateTimeField(blank=True, null=True)
    role_administrator = models.BooleanField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    profile_photo_id = models.IntegerField(blank=True, null=True)
    building = ArrayField(models.CharField(max_length=255), default=list)
    country = models.CharField(max_length=255, blank=True, null=True)
    skype_name = models.CharField(max_length=255, blank=True, null=True)
    key_skills = ArrayField(models.CharField(max_length=255), default=list)
    language_fluent = models.TextField(blank=True, null=True)
    language_intermediate = models.TextField(blank=True, null=True)
    grade = models.TextField(blank=True, null=True)
    previous_positions = models.TextField(blank=True, null=True)
    learning_and_development = ArrayField(
        models.CharField(max_length=255), default=list
    )
    networks = ArrayField(models.CharField(max_length=255), default=list)
    additional_responsibilities = ArrayField(
        models.CharField(max_length=255), default=list
    )
    other_uk = models.TextField(blank=True, null=True)
    other_overseas = models.TextField(blank=True, null=True)
    other_key_skills = models.CharField(max_length=255, blank=True, null=True)
    other_learning_and_development = models.CharField(
        max_length=255, blank=True, null=True
    )
    other_additional_responsibilities = models.CharField(
        max_length=255, blank=True, null=True
    )
    professions = ArrayField(models.CharField(max_length=255), default=list)
    other_professions = models.CharField(max_length=255, blank=True, null=True)
    ditsso_user_id = models.CharField(max_length=255, blank=True, null=True)
    pronouns = models.CharField(max_length=255, blank=True, null=True)
    line_manager_id = models.IntegerField(blank=True, null=True)
    line_manager_not_required = models.BooleanField(blank=True, null=True)
    role_people_editor = models.BooleanField(blank=True, null=True)
    role_groups_editor = models.BooleanField(blank=True, null=True)
    last_edited_or_confirmed_at = models.DateTimeField(blank=True, null=True)
    contact_email = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "people"

    def __str__(self):
        return f"{self.given_name} {self.surname}"


class ProfilePhotos(LegacyPeopleFinderModel):
    image = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "profile_photos"


# class Reports(LegacyPeopleFinderModel):
#     content = models.TextField(blank=True, null=True)
#     name = models.CharField(max_length=-1, blank=True, null=True)
#     extension = models.CharField(max_length=-1, blank=True, null=True)
#     mime_type = models.CharField(max_length=-1, blank=True, null=True)
#     created_at = models.DateTimeField()
#     updated_at = models.DateTimeField()

#     class Meta:
#         managed = False
#         db_table = 'reports'


# class SchemaMigrations(LegacyPeopleFinderModel):
#     version = models.CharField(primary_key=True, max_length=-1)

#     class Meta:
#         managed = False
#         db_table = 'schema_migrations'


# class Versions(LegacyPeopleFinderModel):
#     item_type = models.TextField()
#     item_id = models.IntegerField()
#     event = models.TextField()
#     whodunnit = models.TextField(blank=True, null=True)
#     object = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(blank=True, null=True)
#     object_changes = models.TextField(blank=True, null=True)
#     ip_address = models.CharField(max_length=-1, blank=True, null=True)
#     user_agent = models.CharField(max_length=-1, blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'versions'
