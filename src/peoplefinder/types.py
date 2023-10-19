from django.db import models


class ProfileSections(models.TextChoices):
    CONTACT = "contact", "Contact me"
    ROLE = "role", "My role"
    LOCATION = "location", "Where to find me"
    ABOUT = "about", "About me"


class EditSections(models.TextChoices):
    PERSONAL = "personal", "Personal details"
    CONTACT = "contact", "Contact details"
    TEAMS = "teams", "Team and role"
    LOCATION = "location", "Location and working patterns"
    SKILLS = "skills", "Skills, networks and interests"
    ACCOUNT_SETTINGS = "account_settings", "Account settings"
    ADMIN = "admin", "Administer profile"
