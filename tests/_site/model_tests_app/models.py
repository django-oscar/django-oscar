from django.utils import six
from django.db import models
from oscar.models.fields import AutoSlugField
from oscar.apps.offer.models import Benefit, Condition


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


class BasketOwnerCalledBarry(Condition):

    class Meta:
        proxy = True
        app_label = 'tests'

    def is_satisfied(self, offer, basket):
        if not basket.owner:
            return False
        return basket.owner.first_name.lower() == 'barry'

    def can_apply_condition(self, product):
        return False


class CustomBenefitModel(Benefit):

    name = 'Test benefit'

    class Meta:
        proxy = True
        app_label = 'tests'

    def __str__(self):
        return self.name

    @property
    def description(self):
        return self.name
