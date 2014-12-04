from django.utils import six
from django.db import models
from oscar.models.fields import AutoSlugField


class SluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from='title')


class ChildSluggedTestModel(SluggedTestModel):
    pass


class CustomSluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from='title',
                         separator=six.u("_"),
                         uppercase=True)
