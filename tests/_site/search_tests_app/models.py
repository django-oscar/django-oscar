from django.db import models


class SearchModel(models.Model):

    title = models.CharField(max_length=12)
