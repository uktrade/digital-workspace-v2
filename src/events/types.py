from django.db import models


class EventAudience(models.TextChoices):
    ALL_STAFF = "all", "All staff"
    GRADE_7 = "grade_7", "Grade 7 (G7/D6)"
    GRADE_6 = "grade_6", "Grade 6 (G6/D7)"
    SCS_1 = "scs_1", "Senior civil service 1 (SCS1/SMS1)"
    SCS_2 = "scs_2", "Senior civil service 2 (SCS2/SMS2)"


class EventType(models.TextChoices):
    IN_PERSON = "in_person", "In person"
    ONLINE = "online", "Online"
    HYBRID = "hybrid", "Hybrid"
