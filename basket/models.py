from django.db import models


class Basket(models.Model):
    owner = models.ForeignKey('auth.User')
    status = models.CharField(max_length)
