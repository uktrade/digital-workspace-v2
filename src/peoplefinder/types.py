from django.db import models


class EditSections(models.TextChoices):
    PERSONAL = "personal", "Personal Details"
    CONTACT = "contact", "Contact Details"
    TEAMS = "teams", "Team and role"
    LOCATION = "location", "Location and working patterns"
    SKILLS = "skills", "Skills, Networks and Interests"
    ADMIN = "admin", "Administer profile"
