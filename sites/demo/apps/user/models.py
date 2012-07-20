from django.db import models


class Profile(models.Model):
    """
    Dummy profile model used for testing
    """
    user = models.OneToOneField('auth.User', related_name="profile")
    MALE, FEMALE = 'M', 'F'
    choices = (
        (MALE, 'Male'),
        (FEMALE, 'Female'))
    gender = models.CharField(max_length=1, choices=choices,
                              verbose_name='Gender')
    age = models.PositiveIntegerField(verbose_name='Age')
