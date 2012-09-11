from decimal import Decimal, ROUND_DOWN, ROUND_UP
import math
import datetime

from django.core import exceptions
from django.template.defaultfilters import slugify
from django.db import models
from django.utils.translation import ungettext, ugettext as _
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings

from oscar.apps.offer.managers import ActiveOfferManager
from oscar.models.fields import PositiveDecimalField, ExtendedURLField


class AbstractConditionalOffer(models.Model):
    """
    A conditional offer (eg buy 1, get 10% off)
    """
    name = models.CharField(_("Name"), max_length=128, unique=True,
                            help_text=_("""This is displayed within the customer's
                            basket"""))
    slug = models.SlugField(_("Slug"), max_length=128, unique=True, null=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    # Offers come in a few different types:
    # (a) Offers that are available to all customers on the site.  Eg a
    #     3-for-2 offer.
    # (b) Offers that are linked to a voucher, and only become available once
    #     that voucher has been applied to the basket
    # (c) Offers that are linked to a user.  Eg, all students get 10% off.  The code
    #     to apply this offer needs to be coded
    # (d) Session offers - these are temporarily available to a user after some trigger
    #     event.  Eg, users coming from some affiliate site get 10% off.
    SITE, VOUCHER, USER, SESSION = ("Site", "Voucher", "User", "Session")
    TYPE_CHOICES = (
        (SITE, _("Site offer - available to all users")),
        (VOUCHER, _("Voucher offer - only available after entering the appropriate voucher code")),
        (USER, _("User offer - available to certain types of user")),
        (SESSION, _("Session offer - temporary offer, available for a user for the duration of their session")),
    )
    offer_type = models.CharField(_("Type"), choices=TYPE_CHOICES, default=SITE, max_length=128)

    condition = models.ForeignKey('offer.Condition', verbose_name=_("Condition"))
    benefit = models.ForeignKey('offer.Benefit', verbose_name=_("Benefit"))

    # Range of availability.  Note that if this is a voucher offer, then these
    # dates are ignored and only the dates from the voucher are used to determine
    # availability.
    start_date = models.DateField(_("Start Date"), blank=True, null=True)
    end_date = models.DateField(_("End Date"), blank=True, null=True,
                                help_text=_("Offers are not active on their end "
                                            "date, only the days preceding"))

    # Some complicated situations require offers to be applied in a set order.
    priority = models.IntegerField(_("Priority"), default=0,
        help_text=_("The highest priority offers are applied first"))

    # We track some information on usage
    total_discount = models.DecimalField(_("Total Discount"), decimal_places=2, max_digits=12, default=Decimal('0.00'))
    num_orders = models.PositiveIntegerField(_("Number of Orders"), default=0)

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    redirect_url = ExtendedURLField(_("URL redirect (optional)"), blank=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    # We need to track the voucher that this offer came from (if it is a voucher offer)
    _voucher = None

    class Meta:
        abstract = True
        ordering = ['-priority']
        verbose_name = _("Conditional Offer")
        verbose_name_plural = _("Conditional Offers")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(AbstractConditionalOffer, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('offer:detail', kwargs={'slug': self.slug})

    def __unicode__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise exceptions.ValidationError(_('End date should be later than start date'))

    def is_active(self, test_date=None):
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date

    def is_condition_satisfied(self, basket):
        return self._proxy_condition().is_satisfied(basket)

    def is_condition_partially_satisfied(self, basket):
        return self._proxy_condition().is_partially_satisfied(basket)

    def get_upsell_message(self, basket):
        return self._proxy_condition().get_upsell_message(basket)

    def apply_benefit(self, basket):
        """
        Applies the benefit to the given basket and returns the discount.
        """
        if not self.is_condition_satisfied(basket):
            return Decimal('0.00')
        return self._proxy_benefit().apply(basket, self._proxy_condition())

    def set_voucher(self, voucher):
        self._voucher = voucher

    def get_voucher(self):
        return self._voucher

    def _proxy_condition(self):
        """
        Returns the appropriate proxy model for the condition
        """
        field_dict = dict(self.condition.__dict__)
        if '_state' in field_dict:
            del field_dict['_state']
        if '_range_cache' in field_dict:
            del field_dict['_range_cache']
        if self.condition.type == self.condition.COUNT:
            CountCondition = models.get_model('offer', 'CountCondition')
            return CountCondition(**field_dict)
        elif self.condition.type == self.condition.VALUE:
            ValueCondition = models.get_model('offer', 'ValueCondition')
            return ValueCondition(**field_dict)
        elif self.condition.type == self.condition.COVERAGE:
            CoverageCondition = models.get_model('offer', 'CoverageCondition')
            return CoverageCondition(**field_dict)
        return self.condition

    def _proxy_benefit(self):
        """
        Returns the appropriate proxy model for the condition
        """
        field_dict = dict(self.benefit.__dict__)
        if '_state' in field_dict:
            del field_dict['_state']
        if self.benefit.type == self.benefit.PERCENTAGE:
            PercentageDiscountBenefit = models.get_model('offer', 'PercentageDiscountBenefit')
            return PercentageDiscountBenefit(**field_dict)
        elif self.benefit.type == self.benefit.FIXED:
            AbsoluteDiscountBenefit = models.get_model('offer', 'AbsoluteDiscountBenefit')
            return AbsoluteDiscountBenefit(**field_dict)
        elif self.benefit.type == self.benefit.MULTIBUY:
            MultibuyDiscountBenefit = models.get_model('offer', 'MultibuyDiscountBenefit')
            return MultibuyDiscountBenefit(**field_dict)
        elif self.benefit.type == self.benefit.FIXED_PRICE:
            FixedPriceBenefit = models.get_model('offer', 'FixedPriceBenefit')
            return FixedPriceBenefit(**field_dict)
        return self.benefit

    def record_usage(self, discount):
        self.num_orders += 1
        self.total_discount += discount
        self.save()


class AbstractCondition(models.Model):
    COUNT, VALUE, COVERAGE = ("Count", "Value", "Coverage")
    TYPE_CHOICES = (
        (COUNT, _("Depends on number of items in basket that are in condition range")),
        (VALUE, _("Depends on value of items in basket that are in condition range")),
        (COVERAGE, _("Needs to contain a set number of DISTINCT items from the condition range"))
    )
    range = models.ForeignKey('offer.Range', verbose_name=_("Range"))
    type = models.CharField(_('Type'), max_length=128, choices=TYPE_CHOICES)
    value = PositiveDecimalField(_('Value'), decimal_places=2, max_digits=12)

    class Meta:
        abstract = True
        verbose_name = _("Condition")
        verbose_name_plural = _("Conditions")

    def __unicode__(self):
        if self.type == self.COUNT:
            return _("Basket includes %(count)d item(s) from %(range)s") % {
                'count': self.value, 'range': unicode(self.range).lower()}
        elif self.type == self.COVERAGE:
            return _("Basket includes %(count)d distinct products from %(range)s") % {
                'count': self.value, 'range': unicode(self.range).lower()}
        return _("Basket includes %(count)d value from %(range)s") % {
                'count': self.value, 'range': unicode(self.range).lower()}

    description = __unicode__

    def consume_items(self, basket, lines=None):
        raise NotImplementedError("This method should never be called - "
                                  "ensure you are using the correct proxy model")

    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition.  This is
        stubbed in this top-class object.  The subclassing proxies are
        responsible for implementing it correctly.
        """
        return False

    def is_partially_satisfied(self, basket):
        """
        Determine if the basket partially meets the condition.  This is useful
        for up-selling messages to entice customers to buy something more in
        order to qualify for an offer.
        """
        return False

    def get_upsell_message(self, basket):
        return None

    def can_apply_condition(self, product):
        """
            Determines whether the condition can be applied to a given product
        """
        return (self.range.contains_product(product)
                and product.is_discountable)


class AbstractBenefit(models.Model):
    PERCENTAGE, FIXED, MULTIBUY, FIXED_PRICE = ("Percentage", "Absolute", "Multibuy", "Fixed price")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a %% of the product's value")),
        (FIXED, _("Discount is a fixed amount off the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free")),
        (FIXED_PRICE, _("Get the products that meet the condition for a fixed price")),
    )
    range = models.ForeignKey('offer.Range', null=True, blank=True, verbose_name=_("Range"))
    type = models.CharField(_("Type"), max_length=128, choices=TYPE_CHOICES)
    value = PositiveDecimalField(_("Value"), decimal_places=2, max_digits=12,
                                 null=True, blank=True)

    price_field = 'price_incl_tax'

    # If this is not set, then there is no upper limit on how many products
    # can be discounted by this benefit.
    max_affected_items = models.PositiveIntegerField(_("Max Affected Items"), blank=True, null=True,
        help_text=_("Set this to prevent the discount consuming all items within the range that are in the basket."))

    class Meta:
        abstract = True
        verbose_name = _("Benefit")
        verbose_name_plural = _("Benefits")

    def __unicode__(self):
        if self.type == self.PERCENTAGE:
            desc = _("%(value)s%% discount on %(range)s") % {'value': self.value, 'range': unicode(self.range).lower()}
        elif self.type == self.MULTIBUY:
            desc = _("Cheapest product is free from %s") % unicode(self.range).lower()
        elif self.type == self.FIXED_PRICE:
            desc = _("The products that meet the condition are sold for %s") % self.value
        else:
            desc = _("%(value).2f discount on %(range)s") % {'value': float(self.value),
                                                             'range': unicode(self.range).lower()}

        if self.max_affected_items:
            desc += ungettext(" (max 1 item)", " (max %d items)", self.max_affected_items) % self.max_affected_items

        return desc

    description = __unicode__

    def apply(self, basket, condition=None):
        return Decimal('0.00')

    def clean(self):
        if self.value is None:
            if not self.type:
                raise ValidationError(_("Benefit requires a value"))
            elif self.type != self.MULTIBUY:
                raise ValidationError(_("Benefits of type %s need a value") % self.type)
        elif self.value > 100 and self.type == 'Percentage':
            raise ValidationError(_("Percentage benefit value can't be greater than 100"))
        # All benefits need a range apart from FIXED_PRICE
        if self.type and self.type != self.FIXED_PRICE and not self.range:
            raise ValidationError(_("Benefits of type %s need a range") % self.type)

    def round(self, amount):
        """
        Apply rounding to discount amount
        """
        if hasattr(settings, 'OSCAR_OFFER_ROUNDING_FUNCTION'):
            return settings.OSCAR_OFFER_ROUNDING_FUNCTION(amount)
        return amount.quantize(Decimal('.01'), ROUND_DOWN)

    def _effective_max_affected_items(self):
        if not self.max_affected_items:
            max_affected_items = 10000
        else:
            max_affected_items = self.max_affected_items
        return max_affected_items

    def can_apply_benefit(self, product):
        """
            Determines whether the benefit can be applied to a given product
        """
        return product.is_discountable


class AbstractRange(models.Model):
    """
    Represents a range of products that can be used within an offer
    """
    name = models.CharField(_("Name"), max_length=128, unique=True)
    includes_all_products = models.BooleanField(_('Includes All Products'), default=False)
    included_products = models.ManyToManyField('catalogue.Product', related_name='includes', blank=True,
        verbose_name=_("Included Products"))
    excluded_products = models.ManyToManyField('catalogue.Product', related_name='excludes', blank=True,
        verbose_name=_("Excluded Products"))
    classes = models.ManyToManyField('catalogue.ProductClass', related_name='classes', blank=True,
        verbose_name=_("Product Classes"))
    included_categories = models.ManyToManyField('catalogue.Category', related_name='includes', blank=True,
        verbose_name=_("Included Categories"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    __included_product_ids = None
    __excluded_product_ids = None
    __class_ids = None

    class Meta:
        abstract = True
        verbose_name = _("Range")
        verbose_name_plural = _("Ranges")

    def __unicode__(self):
        return self.name

    def contains_product(self, product):
        """
        Check whether the passed product is part of this range
        """
        # We look for shortcircuit checks first before
        # the tests that require more database queries.

        if settings.OSCAR_OFFER_BLACKLIST_PRODUCT and \
            settings.OSCAR_OFFER_BLACKLIST_PRODUCT(product):
            return False
        excluded_product_ids = self._excluded_product_ids()
        if product.id in excluded_product_ids:
            return False
        if self.includes_all_products:
            return True
        if product.product_class_id in self._class_ids():
            return True
        included_product_ids = self._included_product_ids()
        if product.id in included_product_ids:
            return True
        test_categories = self.included_categories.all()
        if test_categories:
            for category in product.categories.all():
                for test_category in test_categories:
                    if category == test_category or category.is_descendant_of(test_category):
                        return True
        return False

    def _included_product_ids(self):
        if None == self.__included_product_ids:
            self.__included_product_ids = [row['id'] for row in self.included_products.values('id')]
        return self.__included_product_ids

    def _excluded_product_ids(self):
        if None == self.__excluded_product_ids:
            self.__excluded_product_ids = [row['id'] for row in self.excluded_products.values('id')]
        return self.__excluded_product_ids

    def _class_ids(self):
        if None == self.__class_ids:
            self.__class_ids = [row['id'] for row in self.classes.values('id')]
        return self.__class_ids

    def num_products(self):
        if self.includes_all_products:
            return None
        return self.included_products.all().count()
