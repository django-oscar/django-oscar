# pylint: disable=unused-argument, W0621
import csv
import operator
from decimal import ROUND_DOWN
from decimal import Decimal as D

from django.conf import settings
from django.core import exceptions
from django.db import models
from django.db.models.query import Q
from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext_lazy as _

from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import cached_import_string, get_class, get_classes, get_model
from oscar.models import fields
from oscar.templatetags.currency_filters import currency

ExpandDownwardsCategoryQueryset = get_class(
    "catalogue.expressions", "ExpandDownwardsCategoryQueryset"
)
ActiveOfferManager, RangeManager, BrowsableRangeManager = get_classes(
    "offer.managers", ["ActiveOfferManager", "RangeManager", "BrowsableRangeManager"]
)
ZERO_DISCOUNT = get_class("offer.results", "ZERO_DISCOUNT")
load_proxy, unit_price = get_classes("offer.utils", ["load_proxy", "unit_price"])


class BaseOfferMixin(models.Model):
    class Meta:
        abstract = True

    def proxy(self):
        """
        Return the proxy model
        """
        klassmap = self.proxy_map
        # Short-circuit logic if current class is already a proxy class.
        if self.__class__ in klassmap.values():
            return self

        field_dict = dict(self.__dict__)
        for field in list(field_dict.keys()):
            if field.startswith("_"):
                del field_dict[field]

        if self.proxy_class:
            klass = load_proxy(self.proxy_class)
            # Short-circuit again.
            if self.__class__ == klass:
                return self
            return klass(**field_dict)
        if self.type in klassmap:
            return klassmap[self.type](**field_dict)
        raise RuntimeError(
            "Unrecognised %s type (%s)" % (self.__class__.__name__.lower(), self.type)
        )

    def __str__(self):
        return self.name

    @property
    def name(self):
        """
        A text description of the benefit/condition. Every proxy class
        has to implement it.

        This is used in the dropdowns within the offer dashboard.
        """
        proxy_instance = self.proxy()
        if self.proxy_class and self.__class__ == proxy_instance.__class__:
            raise AssertionError("Name property is not defined on proxy class.")
        return proxy_instance.name

    @property
    def description(self):
        """
        A description of the benefit/condition.
        Defaults to the name. May contain HTML.
        """
        return self.name


class AbstractConditionalOffer(models.Model):
    """
    A conditional offer (e.g. buy 1, get 10% off)
    """

    name = models.CharField(
        _("Name"),
        max_length=128,
        unique=True,
        help_text=_("This is displayed within the customer's basket"),
    )
    slug = fields.AutoSlugField(
        _("Slug"), max_length=128, unique=True, populate_from="name"
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("This is displayed on the offer browsing page"),
    )

    # Offers come in a few different types:
    # (a) Offers that are available to all customers on the site. e.g. a
    #     3-for-2 offer.
    # (b) Offers that are linked to a voucher, and only become available once
    #     that voucher has been applied to the basket
    # (c) Offers that are linked to a user.  e.g. all students get 10% off.  The
    #     code to apply this offer needs to be coded
    # (d) Session offers - these are temporarily available to a user after some
    #     trigger event.  e.g. users coming from some affiliate site get 10%
    #     off.
    SITE, VOUCHER, USER, SESSION = ("Site", "Voucher", "User", "Session")
    TYPE_CHOICES = (
        (SITE, _("Site offer - available to all users")),
        (
            VOUCHER,
            _(
                "Voucher offer - only available after entering "
                "the appropriate voucher code"
            ),
        ),
        (USER, _("User offer - available to certain types of user")),
        (
            SESSION,
            _(
                "Session offer - temporary offer, available for "
                "a user for the duration of their session"
            ),
        ),
    )
    offer_type = models.CharField(
        _("Type"), choices=TYPE_CHOICES, default=SITE, max_length=128
    )

    exclusive = models.BooleanField(
        _("Exclusive offer"),
        help_text=_("Exclusive offers cannot be combined on the same items"),
        default=True,
    )
    combinations = models.ManyToManyField(
        "offer.ConditionalOffer",
        help_text=_(
            "Select other non-exclusive offers that this offer can be combined with on the same items"
        ),
        related_name="in_combination",
        limit_choices_to={"exclusive": False},
        blank=True,
    )

    # We track a status variable so it's easier to load offers that are
    # 'available' in some sense.
    OPEN, SUSPENDED, CONSUMED = "Open", "Suspended", "Consumed"
    status = models.CharField(_("Status"), max_length=64, default=OPEN)

    condition = models.ForeignKey(
        "offer.Condition",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name=_("Condition"),
    )
    benefit = models.ForeignKey(
        "offer.Benefit",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name=_("Benefit"),
    )

    # Some complicated situations require offers to be applied in a set order.
    priority = models.IntegerField(
        _("Priority"),
        default=0,
        db_index=True,
        help_text=_("The highest priority offers are applied first"),
    )

    # AVAILABILITY

    # Range of availability.  Note that if this is a voucher offer, then these
    # dates are ignored and only the dates from the voucher are used to
    # determine availability.
    start_datetime = models.DateTimeField(
        _("Start date"),
        blank=True,
        null=True,
        help_text=_(
            "Offers are active from the start date. "
            "Leave this empty if the offer has no start date."
        ),
    )
    end_datetime = models.DateTimeField(
        _("End date"),
        blank=True,
        null=True,
        help_text=_(
            "Offers are active until the end date. "
            "Leave this empty if the offer has no expiry date."
        ),
    )

    # Use this field to limit the number of times this offer can be applied in
    # total.  Note that a single order can apply an offer multiple times so
    # this is not necessarily the same as the number of orders that can use it.
    # Also see max_basket_applications.
    max_global_applications = models.PositiveIntegerField(
        _("Max global applications"),
        help_text=_(
            "The number of times this offer can be used before it is unavailable"
        ),
        blank=True,
        null=True,
    )

    # Use this field to limit the number of times this offer can be used by a
    # single user.  This only works for signed-in users - it doesn't really
    # make sense for sites that allow anonymous checkout.
    max_user_applications = models.PositiveIntegerField(
        _("Max user applications"),
        help_text=_("The number of times a single user can use this offer"),
        blank=True,
        null=True,
    )

    # Use this field to limit the number of times this offer can be applied to
    # a basket (and hence a single order). Often, an offer should only be
    # usable once per basket/order, so this field will commonly be set to 1.
    max_basket_applications = models.PositiveIntegerField(
        _("Max basket applications"),
        blank=True,
        null=True,
        help_text=_(
            "The number of times this offer can be applied to a basket (and order)"
        ),
    )

    # Use this field to limit the amount of discount an offer can lead to.
    # This can be helpful with budgeting.
    max_discount = models.DecimalField(
        _("Max discount"),
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text=_(
            "When an offer has given more discount to orders "
            "than this threshold, then the offer becomes "
            "unavailable"
        ),
    )

    # TRACKING
    # These fields are used to enforce the limits set by the
    # max_* fields above.

    total_discount = models.DecimalField(
        _("Total Discount"), decimal_places=2, max_digits=12, default=D("0.00")
    )
    num_applications = models.PositiveIntegerField(
        _("Number of applications"), default=0
    )
    num_orders = models.PositiveIntegerField(_("Number of Orders"), default=0)

    redirect_url = fields.ExtendedURLField(_("URL redirect (optional)"), blank=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    # We need to track the voucher that this offer came from (if it is a
    # voucher offer)
    _voucher = None

    class Meta:
        abstract = True
        app_label = "offer"
        ordering = ["-priority", "pk"]
        verbose_name = _("Conditional offer")
        verbose_name_plural = _("Conditional offers")

    def save(self, *args, **kwargs):
        # Check to see if consumption thresholds have been broken
        if not self.is_suspended:
            if self.get_max_applications() == 0:
                self.status = self.CONSUMED
            else:
                self.status = self.OPEN

        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("offer:detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name

    def clean(self):
        if (
            self.start_datetime
            and self.end_datetime
            and self.start_datetime > self.end_datetime
        ):
            raise exceptions.ValidationError(
                _("End date should be later than start date")
            )

    @property
    def is_voucher_offer_type(self):
        return self.offer_type == self.VOUCHER

    @property
    def is_open(self):
        return self.status == self.OPEN

    @property
    def is_suspended(self):
        return self.status == self.SUSPENDED

    def suspend(self):
        self.status = self.SUSPENDED
        self.save()

    suspend.alters_data = True

    def unsuspend(self):
        self.status = self.OPEN
        self.save()

    unsuspend.alters_data = True

    def is_available(self, user=None, test_date=None):
        """
        Test whether this offer is available to be used
        """
        if self.is_suspended:
            return False
        if test_date is None:
            test_date = now()
        predicates = []
        if self.start_datetime:
            predicates.append(self.start_datetime > test_date)
        if self.end_datetime:
            predicates.append(test_date > self.end_datetime)
        if any(predicates):
            return False
        return self.get_max_applications(user) > 0

    def is_condition_satisfied(self, basket):
        return self.condition.proxy().is_satisfied(self, basket)

    def is_condition_partially_satisfied(self, basket):
        return self.condition.proxy().is_partially_satisfied(self, basket)

    def get_upsell_message(self, basket):
        return self.condition.proxy().get_upsell_message(self, basket)

    def apply_benefit(self, basket):
        """
        Applies the benefit to the given basket and returns the discount.
        """
        if not self.is_condition_satisfied(basket):
            return ZERO_DISCOUNT
        return self.benefit.proxy().apply(basket, self.condition.proxy(), self)

    def apply_deferred_benefit(self, basket, order, application):
        """
        Applies any deferred benefits.  These are things like adding loyalty
        points to someone's account.
        """
        return self.benefit.proxy().apply_deferred(basket, order, application)

    def set_voucher(self, voucher):
        self._voucher = voucher

    def get_voucher(self):
        return self._voucher

    def get_max_applications(self, user=None):
        """
        Return the number of times this offer can be applied to a basket for a
        given user.
        """
        if self.max_discount and self.total_discount >= self.max_discount:
            return 0

        # Hard-code a maximum value as we need some sensible upper limit for
        # when there are not other caps.
        limits = [10000]
        if self.max_user_applications and user:
            limits.append(
                max(
                    0, self.max_user_applications - self.get_num_user_applications(user)
                )
            )
        if self.max_basket_applications:
            limits.append(self.max_basket_applications)
        if self.max_global_applications:
            limits.append(max(0, self.max_global_applications - self.num_applications))
        return min(limits)

    def get_num_user_applications(self, user):
        OrderDiscount = get_model("order", "OrderDiscount")
        aggregates = OrderDiscount.objects.filter(
            offer_id=self.id, order__user=user
        ).aggregate(total=models.Sum("frequency"))
        return aggregates["total"] if aggregates["total"] is not None else 0

    def shipping_discount(self, charge, currency=None):
        return self.benefit.proxy().shipping_discount(charge, currency)

    def record_usage(self, discount):
        self.num_applications += discount["freq"]
        self.total_discount += discount["discount"]
        self.num_orders += 1
        self.save()

    record_usage.alters_data = True

    def availability_description(self):
        """
        Return a description of when this offer is available
        """
        restrictions = self.availability_restrictions()
        descriptions = [r["description"] for r in restrictions]
        return "<br/>".join(descriptions)

    def availability_restrictions(self):
        restrictions = []
        if self.is_suspended:
            restrictions.append(
                {"description": _("Offer is suspended"), "is_satisfied": False}
            )

        if self.max_global_applications:
            remaining = self.max_global_applications - self.num_applications
            desc = _("Limited to %(total)d uses (%(remainder)d remaining)") % {
                "total": self.max_global_applications,
                "remainder": remaining,
            }
            restrictions.append({"description": desc, "is_satisfied": remaining > 0})

        if self.max_user_applications:
            if self.max_user_applications == 1:
                desc = _("Limited to 1 use per user")
            else:
                desc = _("Limited to %(total)d uses per user") % {
                    "total": self.max_user_applications
                }
            restrictions.append({"description": desc, "is_satisfied": True})

        if self.max_basket_applications:
            if self.max_user_applications == 1:
                desc = _("Limited to 1 use per basket")
            else:
                desc = _("Limited to %(total)d uses per basket") % {
                    "total": self.max_basket_applications
                }
            restrictions.append({"description": desc, "is_satisfied": True})

        def hide_time_if_zero(dt):
            # Only show hours/minutes if they have been specified
            if dt.tzinfo:
                localtime = dt.astimezone(get_current_timezone())
            else:
                localtime = dt
            if localtime.hour == 0 and localtime.minute == 0:
                return date_filter(localtime, settings.DATE_FORMAT)
            return date_filter(localtime, settings.DATETIME_FORMAT)

        if self.start_datetime or self.end_datetime:
            today = now()
            is_satisfied = False
            if self.start_datetime and self.end_datetime:
                desc = _("Available between %(start)s and %(end)s") % {
                    "start": hide_time_if_zero(self.start_datetime),
                    "end": hide_time_if_zero(self.end_datetime),
                }
                is_satisfied = self.start_datetime <= today <= self.end_datetime
            elif self.start_datetime:
                desc = _("Available from %(start)s") % {
                    "start": hide_time_if_zero(self.start_datetime)
                }
                is_satisfied = today >= self.start_datetime
            elif self.end_datetime:
                desc = _("Available until %(end)s") % {
                    "end": hide_time_if_zero(self.end_datetime)
                }
                is_satisfied = today <= self.end_datetime
            restrictions.append({"description": desc, "is_satisfied": is_satisfied})

        if self.max_discount:
            desc = _("Limited to a cost of %(max)s") % {
                "max": currency(self.max_discount)
            }
            restrictions.append(
                {
                    "description": desc,
                    "is_satisfied": self.total_discount < self.max_discount,
                }
            )

        return restrictions

    @property
    def has_products(self):
        return self.condition.range is not None

    def products(self):
        """
        Return a queryset of products in this offer
        """
        Product = get_model("catalogue", "Product")
        if not self.has_products:
            return Product.objects.none()

        queryset = self.condition.range.all_products()
        return queryset.filter(is_discountable=True).browsable()

    @cached_property
    def combined_offers(self):
        return self.__class__.objects.filter(
            models.Q(pk=self.pk)
            | models.Q(pk__in=self.combinations.values_list("pk", flat=True))
            | models.Q(pk__in=self.in_combination.values_list("pk", flat=True))
        ).distinct()


class AbstractBenefit(BaseOfferMixin, models.Model):
    range = models.ForeignKey(
        "offer.Range",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Range"),
    )

    # Benefit types
    PERCENTAGE, FIXED, FIXED_UNIT, MULTIBUY, FIXED_PRICE = (
        "Percentage",
        "Absolute",
        "Fixed",
        "Multibuy",
        "Fixed price",
    )
    SHIPPING_PERCENTAGE, SHIPPING_ABSOLUTE, SHIPPING_FIXED_PRICE = (
        "Shipping percentage",
        "Shipping absolute",
        "Shipping fixed price",
    )
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a percentage off of the product's value")),
        (FIXED, _("Discount is a fixed amount off of the basket's total")),
        (FIXED_UNIT, _("Discount is a fixed amount off of the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free")),
        (FIXED_PRICE, _("Get the products that meet the condition for a fixed price")),
        (SHIPPING_ABSOLUTE, _("Discount is a fixed amount of the shipping cost")),
        (SHIPPING_FIXED_PRICE, _("Get shipping for a fixed price")),
        (
            SHIPPING_PERCENTAGE,
            _("Discount is a percentage off of the shipping cost"),
        ),
    )
    type = models.CharField(_("Type"), max_length=128, choices=TYPE_CHOICES, blank=True)

    # The value to use with the designated type.  This can be either an integer
    # (eg for multibuy) or a decimal (eg an amount) which is slightly
    # confusing.
    value = fields.PositiveDecimalField(
        _("Value"), decimal_places=2, max_digits=12, null=True, blank=True
    )

    # If this is not set, then there is no upper limit on how many products
    # can be discounted by this benefit.
    max_affected_items = models.PositiveIntegerField(
        _("Max Affected Items"),
        blank=True,
        null=True,
        help_text=_(
            "Set this to prevent the discount consuming all items "
            "within the range that are in the basket."
        ),
    )

    # A custom benefit class can be used instead.  This means the
    # type/value/max_affected_items fields should all be None.
    proxy_class = fields.NullCharField(_("Custom class"), max_length=255, default=None)

    class Meta:
        abstract = True
        app_label = "offer"
        verbose_name = _("Benefit")
        verbose_name_plural = _("Benefits")

    @property
    def proxy_map(self):
        return {
            self.PERCENTAGE: get_class("offer.benefits", "PercentageDiscountBenefit"),
            self.FIXED: get_class("offer.benefits", "AbsoluteDiscountBenefit"),
            self.FIXED_UNIT: get_class("offer.benefits", "FixedUnitDiscountBenefit"),
            self.MULTIBUY: get_class("offer.benefits", "MultibuyDiscountBenefit"),
            self.FIXED_PRICE: get_class("offer.benefits", "FixedPriceBenefit"),
            self.SHIPPING_ABSOLUTE: get_class(
                "offer.benefits", "ShippingAbsoluteDiscountBenefit"
            ),
            self.SHIPPING_FIXED_PRICE: get_class(
                "offer.benefits", "ShippingFixedPriceBenefit"
            ),
            self.SHIPPING_PERCENTAGE: get_class(
                "offer.benefits", "ShippingPercentageDiscountBenefit"
            ),
        }

    def apply(self, basket, condition, offer):
        return ZERO_DISCOUNT

    def apply_deferred(self, basket, order, application):
        return None

    def clean(self):
        if not self.type:
            return
        method_name = "clean_%s" % self.type.lower().replace(" ", "_")
        if hasattr(self, method_name):
            getattr(self, method_name)()

    def clean_multibuy(self):
        errors = []

        if not self.range:
            errors.append(_("Multibuy benefits require a product range"))
        if self.value:
            errors.append(_("Multibuy benefits don't require a value"))
        if self.max_affected_items:
            errors.append(
                _("Multibuy benefits don't require a 'max affected items' attribute")
            )

        if errors:
            raise exceptions.ValidationError(errors)

    def clean_percentage(self):
        errors = []

        if not self.range:
            errors.append(_("Percentage benefits require a product range"))

        if not self.value:
            errors.append(_("Percentage discount benefits require a value"))
        elif self.value > 100:
            errors.append(_("Percentage discount cannot be greater than 100"))

        if errors:
            raise exceptions.ValidationError(errors)

    def clean_shipping_absolute(self):
        errors = []
        if not self.value:
            errors.append(_("A discount value is required"))
        if self.range:
            errors.append(
                _(
                    "No range should be selected as this benefit does "
                    "not apply to products"
                )
            )
        if self.max_affected_items:
            errors.append(
                _(
                    "Shipping discounts don't require a "
                    "'max affected items' attribute"
                )
            )

        if errors:
            raise exceptions.ValidationError(errors)

    def clean_shipping_percentage(self):
        errors = []

        if not self.value:
            errors.append(_("Percentage discount benefits require a value"))
        elif self.value > 100:
            errors.append(_("Percentage discount cannot be greater than 100"))

        if self.range:
            errors.append(
                _(
                    "No range should be selected as this benefit does "
                    "not apply to products"
                )
            )
        if self.max_affected_items:
            errors.append(
                _(
                    "Shipping discounts don't require a "
                    "'max affected items' attribute"
                )
            )
        if errors:
            raise exceptions.ValidationError(errors)

    def clean_shipping_fixed_price(self):
        errors = []
        if self.range:
            errors.append(
                _(
                    "No range should be selected as this benefit does "
                    "not apply to products"
                )
            )
        if self.max_affected_items:
            errors.append(
                _(
                    "Shipping discounts don't require a "
                    "'max affected items' attribute"
                )
            )

        if errors:
            raise exceptions.ValidationError(errors)

    def clean_fixed_price(self):
        if self.range:
            raise exceptions.ValidationError(
                _(
                    "No range should be selected as the condition range will "
                    "be used instead."
                )
            )

    def clean_absolute(self):
        errors = []
        if not self.range:
            errors.append(_("Fixed discount benefits require a product range"))
        if not self.value:
            errors.append(_("Fixed discount benefits require a value"))

        if errors:
            raise exceptions.ValidationError(errors)

    def clean_fixed(self):
        errors = []
        if not self.range:
            errors.append(
                _("Fixed product level discount benefits require a product range")
            )
        if not self.value:
            errors.append(_("Fixed product level discount benefits require a value"))

        if errors:
            raise exceptions.ValidationError(errors)

    def round(self, amount, currency=None):
        """
        Apply rounding to discount amount
        """
        rounding_function_path = getattr(
            settings, "OSCAR_OFFER_ROUNDING_FUNCTION", None
        )
        if rounding_function_path:
            rounding_function = cached_import_string(rounding_function_path)
            return rounding_function(amount, currency)

        return amount.quantize(D(".01"), ROUND_DOWN)

    def _effective_max_affected_items(self):
        """
        Return the maximum number of items that can have a discount applied
        during the application of this benefit
        """
        return self.max_affected_items if self.max_affected_items else 10000

    def can_apply_benefit(self, line):
        """
        Determines whether the benefit can be applied to a given basket line
        """
        return line.stockrecord and line.product.is_discountable

    # pylint: disable=W0622
    def get_applicable_lines(self, offer, basket, range=None):
        """
        Return the basket lines that are available to be discounted

        :basket: The basket
        :range: The range of products to use for filtering.  The fixed-price
                benefit ignores its range and uses the condition range
        """
        if range is None:
            range = self.range
        line_tuples = []
        for line in basket.all_lines():
            product = line.product

            if not range.contains_product(product) or not self.can_apply_benefit(line):
                continue

            price = unit_price(offer, line)
            if not price:
                # Avoid zero price products
                continue
            line_tuples.append((price, line))

        # We sort lines to be cheapest first to ensure consistent applications
        return sorted(line_tuples, key=operator.itemgetter(0))

    def shipping_discount(self, charge, currency=None):
        return D("0.00")


class AbstractCondition(BaseOfferMixin, models.Model):
    """
    A condition for an offer to be applied. You can either specify a custom
    proxy class, or need to specify a type, range and value.
    """

    COUNT, VALUE, COVERAGE = ("Count", "Value", "Coverage")
    TYPE_CHOICES = (
        (
            COUNT,
            _("Depends on number of items in basket that are in condition range"),
        ),
        (
            VALUE,
            _("Depends on value of items in basket that are in condition range"),
        ),
        (
            COVERAGE,
            _(
                "Needs to contain a set number of DISTINCT items "
                "from the condition range"
            ),
        ),
    )
    range = models.ForeignKey(
        "offer.Range",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Range"),
    )
    type = models.CharField(_("Type"), max_length=128, choices=TYPE_CHOICES, blank=True)
    value = fields.PositiveDecimalField(
        _("Value"), decimal_places=2, max_digits=12, null=True, blank=True
    )

    proxy_class = fields.NullCharField(_("Custom class"), max_length=255, default=None)

    class Meta:
        abstract = True
        app_label = "offer"
        verbose_name = _("Condition")
        verbose_name_plural = _("Conditions")

    @property
    def proxy_map(self):
        return {
            self.COUNT: get_class("offer.conditions", "CountCondition"),
            self.VALUE: get_class("offer.conditions", "ValueCondition"),
            self.COVERAGE: get_class("offer.conditions", "CoverageCondition"),
        }

    def clean(self):
        # The form will validate whether this is ok or not.
        if not self.type:
            return
        method_name = "clean_%s" % self.type.lower()
        if hasattr(self, method_name):
            getattr(self, method_name)()

    def clean_count(self):
        errors = []

        if not self.range:
            errors.append(_("Count conditions require a product range"))

        if not self.value:
            errors.append(_("Count conditions require a value"))

        if errors:
            raise exceptions.ValidationError(errors)

    def clean_value(self):
        errors = []

        if not self.range:
            errors.append(_("Value conditions require a product range"))

        if not self.value:
            errors.append(_("Value conditions require a value"))

        if errors:
            raise exceptions.ValidationError(errors)

    def clean_coverage(self):
        errors = []

        if not self.range:
            errors.append(_("Coverage conditions require a product range"))

        if not self.value:
            errors.append(_("Coverage conditions require a value"))

        if errors:
            raise exceptions.ValidationError(errors)

    def consume_items(self, offer, basket, affected_lines):
        pass

    def is_satisfied(self, offer, basket):
        """
        Determines whether a given basket meets this condition.  This is
        stubbed in this top-class object.  The subclassing proxies are
        responsible for implementing it correctly.
        """
        return False

    def is_partially_satisfied(self, offer, basket):
        """
        Determine if the basket partially meets the condition.  This is useful
        for up-selling messages to entice customers to buy something more in
        order to qualify for an offer.
        """
        return False

    def get_upsell_message(self, offer, basket):
        return None

    def can_apply_condition(self, line):
        """
        Determines whether the condition can be applied to a given basket line
        """
        if not line.stockrecord_id:
            return False
        product = line.product
        return self.range.contains_product(product) and product.is_discountable

    def get_applicable_lines(self, offer, basket, most_expensive_first=True):
        """
        Return line data for the lines that can be consumed by this condition
        """
        line_tuples = []
        for line in basket.all_lines():
            if not self.can_apply_condition(line):
                continue

            price = unit_price(offer, line)
            if not price:
                continue
            line_tuples.append((price, line))
        key = operator.itemgetter(0)
        if most_expensive_first:
            return sorted(line_tuples, reverse=True, key=key)
        return sorted(line_tuples, key=key)


class AbstractRange(models.Model):
    """
    Represents a range of products that can be used within an offer.
    """

    name = models.CharField(_("Name"), max_length=128, unique=True)
    slug = fields.AutoSlugField(
        _("Slug"), max_length=128, unique=True, populate_from="name"
    )

    description = models.TextField(_("Description"), blank=True)

    # Whether this range is public
    is_public = models.BooleanField(
        _("Is public?"),
        default=False,
        help_text=_("Public ranges have a customer-facing page"),
    )

    includes_all_products = models.BooleanField(
        _("Includes all products?"), default=False
    )

    included_products = models.ManyToManyField(
        "catalogue.Product",
        related_name="includes",
        blank=True,
        verbose_name=_("Included Products"),
        through="offer.RangeProduct",
    )
    excluded_products = models.ManyToManyField(
        "catalogue.Product",
        related_name="excludes",
        blank=True,
        verbose_name=_("Excluded Products"),
    )
    classes = models.ManyToManyField(
        "catalogue.ProductClass",
        related_name="classes",
        blank=True,
        verbose_name=_("Product Types"),
    )
    included_categories = models.ManyToManyField(
        "catalogue.Category",
        related_name="includes",
        blank=True,
        verbose_name=_("Included Categories"),
    )
    excluded_categories = models.ManyToManyField(
        "catalogue.Category",
        related_name="excludes",
        blank=True,
        verbose_name=_("Excluded Categories"),
        help_text=_(
            "Products with these categories are excluded from the range when "
            "Includes all products is checked"
        ),
    )

    # Allow a custom range instance to be specified
    proxy_class = fields.NullCharField(
        _("Custom class"), max_length=255, default=None, unique=True
    )

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    objects = RangeManager()
    browsable = BrowsableRangeManager()

    class Meta:
        abstract = True
        app_label = "offer"
        ordering = ["name"]
        verbose_name = _("Range")
        verbose_name_plural = _("Ranges")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalogue:range", kwargs={"slug": self.slug})

    @cached_property
    def proxy(self):
        if self.proxy_class:
            return load_proxy(self.proxy_class)()

    def add_product(self, product, display_order=None):
        """Add product to the range

        When adding product that is already in the range, prevent re-adding it.
        If display_order is specified, update it.

        Default display_order for a new product in the range is 0; this puts
        the product at the top of the list.
        """

        initial_order = display_order or 0
        RangeProduct = self.included_products.through
        relation, __ = RangeProduct.objects.get_or_create(
            range=self, product=product, defaults={"display_order": initial_order}
        )

        if display_order is not None and relation.display_order != display_order:
            relation.display_order = display_order
            relation.save()

        # Remove product from excluded products if it was removed earlier and
        # re-added again, thus it returns back to the range product list.
        self.excluded_products.remove(product)

        # invalidate cache because queryset has changed
        self.invalidate_cached_queryset()

    def remove_product(self, product):
        """
        Remove product from range. To save on queries, this function does not
        check if the product is in fact in the range.
        """
        RangeProduct = self.included_products.through
        RangeProduct.objects.filter(range=self, product=product).delete()
        # Making sure product will be excluded from range products list by adding to
        # respective field. Otherwise, it could be included as a product from included
        # category or etc.
        self.excluded_products.add(product)

        # invalidate cache because queryset has changed
        self.invalidate_cached_queryset()

    def contains_product(self, product):
        if self.proxy:
            return self.proxy.contains_product(product)
        return self.product_queryset.filter(id=product.id).exists()

    def invalidate_cached_queryset(self):
        try:
            del self.product_queryset
        except AttributeError:
            pass

    def num_products(self):
        # Delegate to a proxy class if one is provided
        if self.proxy:
            return self.proxy.num_products()
        if self.includes_all_products:
            return None
        return self.all_products().count()

    def all_products(self):
        """
        Return a queryset containing all the products in the range

        This includes included_products plus the products contained in the
        included classes and categories, minus the products in
        excluded_products.
        """
        if self.proxy:
            return self.proxy.all_products()

        return self.product_queryset

    @cached_property
    def product_queryset(self):
        "cached queryset of all the products in the Range"
        Product = self.included_products.model

        if self.includes_all_products:
            _filter = Q(id__in=self.excluded_products.values("id"))
            # extend filter if excluded_categories exist
            if self.excluded_categories.exists():
                expanded_range_categories = ExpandDownwardsCategoryQueryset(
                    self.excluded_categories.values("id")
                )
                _filter |= Q(categories__in=expanded_range_categories)
                # extend filter for parent categories, exclude parent = None
                if (
                    Product.objects.exclude(parent=None)
                    .filter(parent__categories__in=expanded_range_categories)
                    .exists()
                ):
                    _filter |= Q(parent__categories__in=expanded_range_categories)

            # Filter out blacklisted
            return Product.objects.exclude(_filter)

        # start with filter clause that always applies
        _filter = Q(includes=self)

        # extend filter if included_products have children
        if Product.objects.filter(parent__includes=self).exists():
            _filter |= Q(parent__includes=self)

        # extend filter if included classes exist:
        if self.classes.exists():
            _filter |= Q(product_class__classes=self)
            # this is always very fast so no check is needed
            _filter |= Q(parent__product_class__classes=self)

        # extend filter if included_categories exist
        if self.included_categories.exists():
            expanded_range_categories = ExpandDownwardsCategoryQueryset(
                self.included_categories.values("id")
            )
            _filter |= Q(categories__in=expanded_range_categories)
            # extend filter for parent categories, exclude parent = None
            if (
                Product.objects.exclude(parent=None)
                .filter(parent__categories__in=expanded_range_categories)
                .exists()
            ):
                _filter |= Q(parent__categories__in=expanded_range_categories)

        qs = Product.objects.filter(_filter, ~Q(excludes=self))

        if Product.objects.filter(parent__excludes=self).exists():
            qs = qs.filter(~Q(parent__excludes=self))

        # make sure to filter out duplicates originating from a join
        return qs.distinct()

    @property
    def is_editable(self):
        """
        Test whether this range can be edited in the dashboard.
        """
        return not self.proxy_class

    @property
    def is_reorderable(self):
        """
        Test whether products for the range can be re-ordered.
        """
        return not (
            self.included_categories.exists()
            or self.classes.exists()
            or (self.excluded_categories.exists() and self.includes_all_products)
        )


class AbstractRangeProduct(models.Model):
    """
    Allow ordering products inside ranges
    Exists to allow customising.
    """

    range = models.ForeignKey("offer.Range", on_delete=models.CASCADE)
    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)
    display_order = models.IntegerField(default=0)

    class Meta:
        abstract = True
        app_label = "offer"
        unique_together = ("range", "product")


class AbstractRangeProductFileUpload(models.Model):
    range = models.ForeignKey(
        "offer.Range",
        on_delete=models.CASCADE,
        related_name="file_uploads",
        verbose_name=_("Range"),
    )
    filepath = models.CharField(_("File Path"), max_length=255)
    size = models.PositiveIntegerField(_("Size"))
    uploaded_by = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Uploaded By")
    )
    date_uploaded = models.DateTimeField(
        _("Date Uploaded"), auto_now_add=True, db_index=True
    )

    INCLUDED_PRODUCTS_TYPE = "included"
    EXCLUDED_PRODUCTS_TYPE = "excluded"
    UPLOAD_TYPE_CHOICES = [
        (INCLUDED_PRODUCTS_TYPE, "Included products upload"),
        (EXCLUDED_PRODUCTS_TYPE, "Excluded products upload"),
    ]
    upload_type = models.CharField(
        max_length=8, choices=UPLOAD_TYPE_CHOICES, default=INCLUDED_PRODUCTS_TYPE
    )

    PENDING, FAILED, PROCESSED = "Pending", "Failed", "Processed"
    choices = (
        (PENDING, PENDING),
        (FAILED, FAILED),
        (PROCESSED, PROCESSED),
    )
    status = models.CharField(
        _("Status"), max_length=32, choices=choices, default=PENDING
    )
    error_message = models.CharField(_("Error Message"), max_length=255, blank=True)

    # Post-processing audit fields
    date_processed = models.DateTimeField(_("Date Processed"), null=True)
    num_new_skus = models.PositiveIntegerField(_("Number of New SKUs"), null=True)
    num_unknown_skus = models.PositiveIntegerField(
        _("Number of Unknown SKUs"), null=True
    )
    num_duplicate_skus = models.PositiveIntegerField(
        _("Number of Duplicate SKUs"), null=True
    )

    class Meta:
        abstract = True
        app_label = "offer"
        ordering = ("-date_uploaded",)
        verbose_name = _("Range Product Uploaded File")
        verbose_name_plural = _("Range Product Uploaded Files")

    def mark_as_failed(self, message=None):
        self.date_processed = now()
        self.error_message = message
        self.status = self.FAILED
        self.save()

    def mark_as_processed(self, num_new, num_unknown, num_duplicate):
        self.status = self.PROCESSED
        self.date_processed = now()
        self.num_new_skus = num_new
        self.num_unknown_skus = num_unknown
        self.num_duplicate_skus = num_duplicate
        self.save()

    def was_processing_successful(self):
        return self.status == self.PROCESSED

    def process(self, file_obj):
        """
        Process the file upload and add products to the range
        or add products to range.excluded_products
        """
        all_ids = set(self.extract_ids(file_obj))
        if self.upload_type == self.INCLUDED_PRODUCTS_TYPE:
            products = self.range.all_products()
        elif self.upload_type == self.EXCLUDED_PRODUCTS_TYPE:
            products = self.range.excluded_products.all()
        else:
            raise ValueError("Unable to process upload type: %s" % self.upload_type)
        existing_skus = products.values_list("stockrecords__partner_sku", flat=True)
        existing_skus = set(filter(bool, existing_skus))
        existing_upcs = products.values_list("upc", flat=True)
        existing_upcs = set(filter(bool, existing_upcs))
        existing_ids = existing_skus.union(existing_upcs)
        new_ids = all_ids - existing_ids

        Product = get_model("catalogue", "Product")
        products = Product._default_manager.filter(
            models.Q(stockrecords__partner_sku__in=new_ids) | models.Q(upc__in=new_ids)
        )
        for product in products:
            if self.upload_type == self.INCLUDED_PRODUCTS_TYPE:
                self.range.add_product(product)
            else:
                self.range.excluded_products.add(product)

        # Processing stats
        found_skus = products.values_list("stockrecords__partner_sku", flat=True)
        found_skus = set(filter(bool, found_skus))
        found_upcs = set(filter(bool, products.values_list("upc", flat=True)))
        found_ids = found_skus.union(found_upcs)
        missing_ids = new_ids - found_ids
        dupes = set(all_ids).intersection(existing_ids)

        self.mark_as_processed(products.count(), len(missing_ids), len(dupes))
        return products

    def extract_ids(self, file_obj):
        reader = csv.reader(file_obj)
        for line in reader:
            if line:
                yield from line
