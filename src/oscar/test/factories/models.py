from django.db import models


class Band(models.Model):
    name = models.CharField(max_length=100)


class Member(models.Model):
    name = models.CharField(max_length=100)
    band = models.ForeignKey(Band, models.CASCADE)
