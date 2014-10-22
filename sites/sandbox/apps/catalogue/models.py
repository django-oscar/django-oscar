from django.db import models
from oscar.apps.catalogue import abstract_models

class Foo(models.Model):
    name = models.CharField(max_length=12)


class Product(abstract_models.AbstractProduct):

    things = models.ManyToManyField(Foo)


from oscar.apps.catalogue.models import *  # noqa
