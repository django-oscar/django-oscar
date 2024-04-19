from django.db import models

from oscar.apps.address.models import UserAddress
from oscar.apps.offer.models import Benefit, Condition
from oscar.models.fields import AutoSlugField


class SluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from="title")


class ChildSluggedTestModel(SluggedTestModel):
    pass


class CustomSluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from="title", separator="_", uppercase=True)


class BasketOwnerCalledBarry(Condition):
    class Meta:
        proxy = True
        app_label = "tests"

    def is_satisfied(self, offer, basket):
        if not basket.owner:
            return False
        return basket.owner.first_name.lower() == "barry"

    # pylint: disable=unused-argument
    def can_apply_condition(self, line):
        return False


class BaseOfferModel(models.Model):
    class Meta:
        abstract = True
        app_label = "tests"


class CustomBenefitModel(BaseOfferModel, Benefit):
    name = "Test benefit"

    class Meta:
        proxy = True
        app_label = "tests"

    def __str__(self):
        return self.name

    @property
    def description(self):
        return self.name


class CustomConditionModel(Condition):
    name = "Test condition"

    class Meta:
        proxy = True
        app_label = "tests"

    def is_satisfied(self, offer, basket):
        return True

    # pylint: disable=unused-argument
    def can_apply_condition(self, line):
        return True


class CustomBenefitWithoutName(Benefit):
    class Meta:
        proxy = True
        app_label = "tests"

    description = "test"


class CustomConditionWithoutName(Condition):
    class Meta:
        proxy = True
        app_label = "tests"


class UserAddressModelWithCustomBaseFields(UserAddress):
    class Meta:
        proxy = True
        app_label = "tests"

    base_fields = ["line1", "line4"]


class UserAddressModelWithCustomHashFields(UserAddress):
    class Meta:
        proxy = True
        app_label = "tests"

    hash_fields = ["line1", "line4"]
