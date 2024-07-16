from django.db import models


class PatternLibrary(models.Model):
    """A temporary model to create a permission for the Django Pattern Library

    This model can be deleted if we move away from Django Pattern Library.
    """

    class Meta:
        managed = False
        permissions = [
            ("view_dpl", "Can view the Django Pattern Library"),
        ]
