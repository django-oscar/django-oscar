from decimal import Decimal as D

from django.db import models
from django.core import exceptions
from django.template.defaultfilters import date as date_filter
from oscar.templatetags.currency_filters import currency
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now, get_current_timezone
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings

from oscar.models import fields
from oscar.core.loading import get_model
from oscar.apps.offer.managers import ActiveOfferManager


@python_2_unicode_compatible
class AbstractConditionalOffer(models.Model):
    """
    A conditional offer (eg buy 1, get 10% off)
    """
    name = models.CharField(
        _("Name"), max_length=128, unique=True,
        help_text=_("This is displayed within the customer's basket"))
    slug = fields.AutoSlugField(
        _("Slug"), max_length=128, unique=True, populate_from='name')
    description = models.TextField(_("Description"), blank=True,
                                   help_text=_("This is displayed on the offer"
                                               " browsing page"))

    # Offers come in a few different types:
    # (a) Offers that are available to all customers on the site.  Eg a
    #     3-for-2 offer.
    # (b) Offers that are linked to a voucher, and only become available once
    #     that voucher has been applied to the basket
    # (c) Offers that are linked to a user.  Eg, all students get 10% off.  The
    #     code to apply this offer needs to be coded
    # (d) Session offers - these are temporarily available to a user after some
    #     trigger event.  Eg, users coming from some affiliate site get 10%
    #     off.
    SITE, VOUCHER, USER, SESSION = ("Site", "Voucher", "User", "Session")
    TYPE_CHOICES = (
        (SITE, _("Site offer - available to all users")),
        (VOUCHER, _("Voucher offer - only available after entering "
                    "the appropriate voucher code")),
        (USER, _("User offer - available to certain types of user")),
        (SESSION, _("Session offer - temporary offer, available for "
                    "a user for the duration of their session")),
    )
    offer_type = models.CharField(
        _("Type"), choices=TYPE_CHOICES, default=SITE, max_length=128)

    # We track a status variable so it's easier to load offers that are
    # 'available' in some sense.
    OPEN, SUSPENDED, CONSUMED = "Open", "Suspended", "Consumed"
    status = models.CharField(_("Status"), max_length=64, default=OPEN)

    condition = models.ForeignKey(
        'offer.Condition', verbose_name=_("Condition"))
    benefit = models.ForeignKey('offer.Benefit', verbose_name=_("Benefit"))

    # Some complicated situations require offers to be applied in a set order.
    priority = models.IntegerField(
        _("Priority"), default=0,
        help_text=_("The highest priority offers are applied first"))

    # AVAILABILITY

    # Range of availability.  Note that if this is a voucher offer, then these
    # dates are ignored and only the dates from the voucher are used to
    # determine availability.
    start_datetime = models.DateTimeField(
        _("Start date"), blank=True, null=True)
    end_datetime = models.DateTimeField(
        _("End date"), blank=True, null=True,
        help_text=_("Offers are active until the end of the 'end date'"))

    # Use this field to limit the number of times this offer can be applied in
    # total.  Note that a single order can apply an offer multiple times so
    # this is not the same as the number of orders that can use it.
    max_global_applications = models.PositiveIntegerField(
        _("Max global applications"),
        help_text=_("The number of times this offer can be used before it "
                    "is unavailable"), blank=True, null=True)

    # Use this field to limit the number of times this offer can be used by a
    # single user.  This only works for signed-in users - it doesn't really
    # make sense for sites that allow anonymous checkout.
    max_user_applications = models.PositiveIntegerField(
        _("Max user applications"),
        help_text=_("The number of times a single user can use this offer"),
        blank=True, null=True)

    # Use this field to limit the number of times this offer can be applied to
    # a basket (and hence a single order).
    max_basket_applications = models.PositiveIntegerField(
        _("Max basket applications"),
        blank=True, null=True,
        help_text=_("The number of times this offer can be applied to a "
                    "basket (and order)"))

    # Use this field to limit the amount of discount an offer can lead to.
    # This can be helpful with budgeting.
    max_discount = models.DecimalField(
        _("Max discount"), decimal_places=2, max_digits=12, null=True,
        blank=True,
        help_text=_("When an offer has given more discount to orders "
                    "than this threshold, then the offer becomes "
                    "unavailable"))

    # TRACKING

    total_discount = models.DecimalField(
        _("Total Discount"), decimal_places=2, max_digits=12,
        default=D('0.00'))
    num_applications = models.PositiveIntegerField(
        _("Number of applications"), default=0)
    num_orders = models.PositiveIntegerField(
        _("Number of Orders"), default=0)

    redirect_url = fields.ExtendedURLField(
        _("URL redirect (optional)"), blank=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    # We need to track the voucher that this offer came from (if it is a
    # voucher offer)
    _voucher = None

    class Meta:
        abstract = True
        app_label = 'offer'
        ordering = ['-priority']
        verbose_name = _("Conditional offer")
        verbose_name_plural = _("Conditional offers")

    def save(self, *args, **kwargs):
        # Check to see if consumption thresholds have been broken
        if not self.is_suspended:
            if self.get_max_applications() == 0:
                self.status = self.CONSUMED
            else:
                self.status = self.OPEN

        return super(AbstractConditionalOffer, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('offer:detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

    def clean(self):
        if (self.start_datetime and self.end_datetime and
                self.start_datetime > self.end_datetime):
            raise exceptions.ValidationError(
                _('End date should be later than start date'))

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
    suspend.alters_data = True

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
        return self.benefit.proxy().apply(
            basket, self.condition.proxy(), self)

    def apply_deferred_benefit(self, basket, order, application):
        """
        Applies any deferred benefits.  These are things like adding loyalty
        points to somone's account.
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
            limits.append(max(0, self.max_user_applications -
                          self.get_num_user_applications(user)))
        if self.max_basket_applications:
            limits.append(self.max_basket_applications)
        if self.max_global_applications:
            limits.append(
                max(0, self.max_global_applications - self.num_applications))
        return min(limits)

    def get_num_user_applications(self, user):
        OrderDiscount = get_model('order', 'OrderDiscount')
        aggregates = OrderDiscount.objects.filter(offer_id=self.id,
                                                  order__user=user)\
            .aggregate(total=models.Sum('frequency'))
        return aggregates['total'] if aggregates['total'] is not None else 0

    def shipping_discount(self, charge):
        return self.benefit.proxy().shipping_discount(charge)

    def record_usage(self, discount):
        self.num_applications += discount['freq']
        self.total_discount += discount['discount']
        self.num_orders += 1
        self.save()
    record_usage.alters_data = True

    def availability_description(self):
        """
        Return a description of when this offer is available
        """
        restrictions = self.availability_restrictions()
        descriptions = [r['description'] for r in restrictions]
        return "<br/>".join(descriptions)

    def availability_restrictions(self):  # noqa (too complex (15))
        restrictions = []
        if self.is_suspended:
            restrictions.append({
                'description': _("Offer is suspended"),
                'is_satisfied': False})

        if self.max_global_applications:
            remaining = self.max_global_applications - self.num_applications
            desc = _("Limited to %(total)d uses (%(remainder)d remaining)") \
                % {'total': self.max_global_applications,
                   'remainder': remaining}
            restrictions.append({'description': desc,
                                 'is_satisfied': remaining > 0})

        if self.max_user_applications:
            if self.max_user_applications == 1:
                desc = _("Limited to 1 use per user")
            else:
                desc = _("Limited to %(total)d uses per user") \
                    % {'total': self.max_user_applications}
            restrictions.append({'description': desc,
                                 'is_satisfied': True})

        if self.max_basket_applications:
            if self.max_user_applications == 1:
                desc = _("Limited to 1 use per basket")
            else:
                desc = _("Limited to %(total)d uses per basket") \
                    % {'total': self.max_basket_applications}
            restrictions.append({
                'description': desc,
                'is_satisfied': True})

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
            if self.start_datetime and self.end_datetime:
                desc = _("Available between %(start)s and %(end)s") \
                    % {'start': hide_time_if_zero(self.start_datetime),
                       'end': hide_time_if_zero(self.end_datetime)}
                is_satisfied \
                    = self.start_datetime <= today <= self.end_datetime
            elif self.start_datetime:
                desc = _("Available from %(start)s") % {
                    'start': hide_time_if_zero(self.start_datetime)}
                is_satisfied = today >= self.start_datetime
            elif self.end_datetime:
                desc = _("Available until %(end)s") % {
                    'end': hide_time_if_zero(self.end_datetime)}
                is_satisfied = today <= self.end_datetime
            restrictions.append({
                'description': desc,
                'is_satisfied': is_satisfied})

        if self.max_discount:
            desc = _("Limited to a cost of %(max)s") % {
                'max': currency(self.max_discount)}
            restrictions.append({
                'description': desc,
                'is_satisfied': self.total_discount < self.max_discount})

        return restrictions

    @property
    def has_products(self):
        return self.condition.range is not None

    def products(self):
        """
        Return a queryset of products in this offer
        """
        Product = get_model('catalogue', 'Product')
        if not self.has_products:
            return Product.objects.none()

        cond_range = self.condition.range
        if cond_range.includes_all_products:
            # Return ALL the products
            queryset = Product.browsable
        else:
            queryset = cond_range.included_products
        return queryset.filter(is_discountable=True).exclude(
            structure=Product.CHILD)


# ============
# Result types
# ============


class ApplicationResult(object):
    is_final = is_successful = False
    # Basket discount
    discount = D('0.00')
    description = None

    # Offer applications can affect 3 distinct things
    # (a) Give a discount off the BASKET total
    # (b) Give a discount off the SHIPPING total
    # (a) Trigger a post-order action
    BASKET, SHIPPING, POST_ORDER = 0, 1, 2
    affects = None

    @property
    def affects_basket(self):
        return self.affects == self.BASKET

    @property
    def affects_shipping(self):
        return self.affects == self.SHIPPING

    @property
    def affects_post_order(self):
        return self.affects == self.POST_ORDER


class BasketDiscount(ApplicationResult):
    """
    For when an offer application leads to a simple discount off the basket's
    total
    """
    affects = ApplicationResult.BASKET

    def __init__(self, amount):
        self.discount = amount

    @property
    def is_successful(self):
        return self.discount > 0

    def __str__(self):
        return '<Basket discount of %s>' % self.discount

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.discount)


# Helper global as returning zero discount is quite common
ZERO_DISCOUNT = BasketDiscount(D('0.00'))


class ShippingDiscount(ApplicationResult):
    """
    For when an offer application leads to a discount from the shipping cost
    """
    is_successful = is_final = True
    affects = ApplicationResult.SHIPPING


SHIPPING_DISCOUNT = ShippingDiscount()


class PostOrderAction(ApplicationResult):
    """
    For when an offer condition is met but the benefit is deferred until after
    the order has been placed.  Eg buy 2 books and get 100 loyalty points.
    """
    is_final = is_successful = True
    affects = ApplicationResult.POST_ORDER

    def __init__(self, description):
        self.description = description