from django.db import models


class ProfileSections(models.TextChoices):
    TEAM_AND_ROLE = "team_and_role", "Team and role"
    WAYS_OF_WORKING = "ways_of_working", "Ways of working"
    SKILLS = "skills", "Skills"


class EditSections(models.TextChoices):
    PERSONAL = "personal", "Personal details"
    CONTACT = "contact", "Contact details"
    TEAMS = "teams", "Team and role"
    LOCATION = "location", "Location and working patterns"
    SKILLS = "skills", "Skills, networks and interests"
    ACCOUNT_SETTINGS = "account_settings", "Account settings"
    ADMIN = "admin", "Administer profile"
