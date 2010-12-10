from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _


class ConditionalOffer(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    condition = models.ForeignKey('offer.Condition')
    benefit = models.ForeignKey('offer.Benefit')
    start_date = models.DateField()
    # Offers can be open-ended
    end_date = models.DateField(blank=True)
    priority = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)


class Condition(models.Model):
    COUNT, VALUE = ("Count", "Value")
    TYPE_CHOICES = (
        (COUNT, _("Depends on number of items in basket that are in condition range")),
        (VALUE, _("Depends on value of items in basket that are in condition range")),
    )
    range = models.ForeignKey('offer.Range')
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = models.FloatField()


class Benefit(models.Model):
    PERCENTAGE, FIXED = ("Percentage", "Absolute")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a % of the product's value")),
        (FIXED, _("Discount is a fixed amount off the product's value")),
    )
    range = models.ForeignKey('offer.Range')
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = models.FloatField()


class Range(models.Model):
    name = models.CharField(max_length=128)
    includes_all_products = models.BooleanField(default=False)
    included_products = models.ManyToManyField('product.Item', related_name='includes')
    excluded_products = models.ManyToManyField('product.Item', related_name='excludes')


class Voucher(models.Model):
    """
    A voucher
    """
    code = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    offers = models.ManyToManyField('offer.ConditionalOffer')
    created_date = models.DateTimeField(auto_now_add=True)