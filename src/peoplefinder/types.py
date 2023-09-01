from django.db import models


class ProfileSections(models.TextChoices):
    CONTACT = "contact", "Contact me"
    ROLE = "role", "My role"
    LOCATION = "location", "Where to find me"
    ABOUT = "about", "About me"


class EditSections(models.TextChoices):
    PERSONAL = "personal", "Personal Details"
    CONTACT = "contact", "Contact Details"
    TEAMS = "teams", "Team and role"
    LOCATION = "location", "Location and working patterns"
    SKILLS = "skills", "Skills, Networks and Interests"
    ADMIN = "admin", "Administer profile"
