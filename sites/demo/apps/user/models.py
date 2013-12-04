from django.db import models
from oscar.core import compat


class Profile(models.Model):
    """
    Dummy profile model used for testing
    """
    user = models.OneToOneField(compat.AUTH_USER_MODEL, related_name="profile")
    MALE, FEMALE = 'M', 'F'
    choices = (
        (MALE, 'Male'),
        (FEMALE, 'Female'))
    gender = models.CharField(max_length=1, choices=choices,
                              verbose_name='Gender')
    age = models.PositiveIntegerField(verbose_name='Age')
