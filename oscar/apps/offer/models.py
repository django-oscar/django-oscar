from decimal import Decimal, ROUND_DOWN, ROUND_UP
import math
import datetime

from django.core import exceptions
from django.db import models
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.conf import settings

from oscar.apps.offer.managers import ActiveOfferManager
from oscar.models.fields import PositiveDecimalField, ExtendedURLField

SITE, VOUCHER, USER, SESSION = ("Site", "Voucher", "User", "Session")


class ConditionalOffer(models.Model):
    """
    A conditional offer (eg buy 1, get 10% off)
    """
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)

    # Offers come in a few different types:
    # (a) Offers that are available to all customers on the site.  Eg a 
    #     3-for-2 offer.
    # (b) Offers that are linked to a voucher, and only become available once
    #     that voucher has been applied to the basket
    # (c) Offers that are linked to a user.  Eg, all students get 10% off.  The code
    #     to apply this offer needs to be coded
    # (d) Session offers - these are temporarily available to a user after some trigger 
    #     event.  Eg, users coming from some affiliate site get 10% off.     
    TYPE_CHOICES = (
        (SITE, "Site offer - available to all users"),
        (VOUCHER, "Voucher offer - only available after entering the appropriate voucher code"),
        (USER, "User offer - available to certain types of user"),
        (SESSION, "Session offer - temporary offer, available for a user for the duration of their session"),
    )
    offer_type = models.CharField(_("Type"), choices=TYPE_CHOICES, default=SITE, max_length=128)

    condition = models.ForeignKey('offer.Condition')
    benefit = models.ForeignKey('offer.Benefit')

    # Range of availability.  Note that if this is a voucher offer, then these
    # dates are ignored and only the dates from the voucher are used to determine 
    # availability.
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # Some complicated situations require offers to be applied in a set order.
    priority = models.IntegerField(default=0, help_text="The highest priority offers are applied first")

    # We track some information on usage
    total_discount = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    
    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    redirect_url = ExtendedURLField(_('URL redirect (optional)'), blank=True)

    # We need to track the voucher that this offer came from (if it is a voucher offer)
    _voucher = None

    class Meta:
        ordering = ['-priority']
        
    def __unicode__(self):
        return self.name    

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise exceptions.ValidationError('End date should be later than start date')
        
    def is_active(self, test_date=None):
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date
    
    def is_condition_satisfied(self, basket):
        return self._proxy_condition().is_satisfied(basket)
        
    def apply_benefit(self, basket):
        u"""
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
        u"""
        Returns the appropriate proxy model for the condition
        """
        field_dict = self.condition.__dict__
        if '_state' in field_dict:
            del field_dict['_state']
        if self.condition.type == self.condition.COUNT:
            return CountCondition(**field_dict)
        elif self.condition.type == self.condition.VALUE:
            return ValueCondition(**field_dict)
        elif self.condition.type == self.condition.COVERAGE:
            return CoverageCondition(**field_dict)
        return self.condition
    
    def _proxy_benefit(self):
        u"""
        Returns the appropriate proxy model for the condition
        """
        field_dict = self.benefit.__dict__
        if '_state' in field_dict:
            del field_dict['_state']
        if self.benefit.type == self.benefit.PERCENTAGE:
            return PercentageDiscountBenefit(**field_dict)
        elif self.benefit.type == self.benefit.FIXED:
            return AbsoluteDiscountBenefit(**field_dict)
        elif self.benefit.type == self.benefit.MULTIBUY:
            return MultibuyDiscountBenefit(**field_dict)
        elif self.benefit.type == self.benefit.FIXED_PRICE:
            return FixedPriceBenefit(**field_dict)
        return self.benefit
        

class Condition(models.Model):
    COUNT, VALUE, COVERAGE = ("Count", "Value", "Coverage")
    TYPE_CHOICES = (
        (COUNT, _("Depends on number of items in basket that are in condition range")),
        (VALUE, _("Depends on value of items in basket that are in condition range")),
        (COVERAGE, _("Needs to contain a set number of DISTINCT items from the condition range"))
    )
    range = models.ForeignKey('offer.Range')
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = PositiveDecimalField(decimal_places=2, max_digits=12)

    def __unicode__(self):
        if self.type == self.COUNT:
            return u"Basket includes %d item(s) from %s" % (self.value, unicode(self.range).lower())
        elif self.type == self.COVERAGE:
            return u"Basket includes %d distinct products from %s" % (self.value, unicode(self.range).lower())
        return u"Basket includes %d value from %s" % (self.value, unicode(self.range).lower())
    
    def consume_items(self, basket, lines=None):
        return ()
    
    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition.  This is
        stubbed in this top-class object.  The subclassing proxies are
        responsible for implementing it correctly.
        """
        return False
    

class Benefit(models.Model):
    PERCENTAGE, FIXED, MULTIBUY, FIXED_PRICE = ("Percentage", "Absolute", "Multibuy", "Fixed price")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a % of the product's value")),
        (FIXED, _("Discount is a fixed amount off the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free")),
        (FIXED_PRICE, _("Get the products that meet the condition for a fixed price")),
    )
    range = models.ForeignKey('offer.Range', null=True, blank=True)
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = PositiveDecimalField(decimal_places=2, max_digits=12,
                                 null=True, blank=True)

    price_field = 'price_incl_tax'

    # If this is not set, then there is no upper limit on how many products 
    # can be discounted by this benefit.
    max_affected_items = models.PositiveIntegerField(blank=True, null=True, help_text="""Set this
        to prevent the discount consuming all items within the range that are in the basket.""")
    
    def __unicode__(self):
        if self.type == self.PERCENTAGE:
            desc = u"%s%% discount on %s" % (self.value, unicode(self.range).lower())
        elif self.type == self.MULTIBUY:
            desc = u"Cheapest product is free from %s" % unicode(self.range).lower()
        elif self.type == self.FIXED_PRICE:
            desc = u"The products that meet the condition are sold for %s" % self.value
        else:
            desc = u"%.2f discount on %s" % (float(self.value), unicode(self.range).lower())
        if self.max_affected_items == 1:
            desc += u" (max 1 item)"
        elif self.max_affected_items > 1:
            desc += u" (max %d items)" % self.max_affected_items
        return desc
    
    def apply(self, basket, condition=None):
        return Decimal('0.00')
    
    def clean(self):
        if self.value is None:
            if not self.type:
                raise ValidationError("Benefit requires a value")
            elif self.type != self.MULTIBUY:
                raise ValidationError("Benefits of type %s need a value" % self.type)
        elif self.value > 100 and self.type == 'Percentage':
            raise ValidationError("Percentage benefit value can't be greater than 100")
        # All benefits need a range apart from FIXED_PRICE
        if self.type and self.type != self.FIXED_PRICE and not self.range:
            raise ValidationError("Benefits of type %s need a range" % self.type)

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


class Range(models.Model):
    """
    Represents a range of products that can be used within an offer
    """
    name = models.CharField(_("Name"), max_length=128, unique=True)
    includes_all_products = models.BooleanField(default=False)
    included_products = models.ManyToManyField('catalogue.Product', related_name='includes', blank=True)
    excluded_products = models.ManyToManyField('catalogue.Product', related_name='excludes', blank=True)
    classes = models.ManyToManyField('catalogue.ProductClass', related_name='classes', blank=True)
    included_categories = models.ManyToManyField('catalogue.Category', related_name='includes', blank=True)
    
    __included_product_ids = None
    __excluded_product_ids = None
    __class_ids = None

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
        

class CountCondition(Condition):
    """
    An offer condition dependent on the NUMBER of matching items from the basket.
    """

    class Meta:
        proxy = True

    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition
        """
        num_matches = 0
        for line in basket.all_lines():
            if self.range.contains_product(line.product) and line.quantity_without_discount > 0:
                num_matches += line.quantity_without_discount
            if num_matches >= self.value:
                return True
        return False
    
    def consume_items(self, basket, lines=None, value=None):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.
        """
        lines = lines or basket.all_lines()
        consumed_products = []
        value = self.value if value is None else value
        for line in lines:
            if self.range.contains_product(line.product):
                quantity_to_consume = min(line.quantity_without_discount,
                                          value - len(consumed_products))
                line.consume(quantity_to_consume)
                consumed_products.extend((line.product,)*int(quantity_to_consume))
            if len(consumed_products) == value:
                break
        return consumed_products
        
        
class CoverageCondition(Condition):
    """
    An offer condition dependent on the NUMBER of matching items from the basket.
    """
    class Meta:
        proxy = True

    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition
        """
        covered_ids = []
        for line in basket.all_lines():
            if not line.is_available_for_discount:
                continue
            product = line.product
            if self.range.contains_product(product) and product.id not in covered_ids:
                covered_ids.append(product.id)
            if len(covered_ids) >= self.value:
                return True
        return False
    
    def consume_items(self, basket, lines=None, value=None):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.
        """
        lines = lines or basket.all_lines()
        consumed_products = []
        value = self.value if value is None else value
        for line in basket.all_lines():
            product = line.product
            if (line.is_available_for_discount and self.range.contains_product(product)
                and product not in consumed_products):
                line.consume(1)
                consumed_products.append(line.product)
            if len(consumed_products) >= value:
                break
        return consumed_products
    
    def get_value_of_satisfying_items(self, basket):
        covered_ids = []
        value = Decimal('0.00')
        for line in basket.all_lines():
            if self.range.contains_product(line.product) and line.product.id not in covered_ids:
                covered_ids.append(line.product.id)
                value += line.unit_price_incl_tax
            if len(covered_ids) >= self.value:
                return value
        return value
        
        
class ValueCondition(Condition):
    """
    An offer condition dependent on the VALUE of matching items from the basket.
    """
    price_field = 'price_incl_tax'

    class Meta:
        proxy = True

    def is_satisfied(self, basket):
        """Determines whether a given basket meets this condition"""
        value_of_matches = Decimal('0.00')
        for line in basket.all_lines():
            product = line.product
            if self.range.contains_product(product) and product.has_stockrecord and line.quantity_without_discount > 0:
                price = getattr(product.stockrecord, self.price_field)
                value_of_matches += price * int(line.quantity_without_discount)
            if value_of_matches >= self.value:
                return True
        return False
    
    def consume_items(self, basket, lines=None, value=None):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.
        
        We allow lines to be passed in as sometimes we want them sorted
        in a specific order.
        """
        value_of_matches = Decimal('0.00')
        lines = lines or basket.all_lines()
        consumed_products = []
        value = self.value if value is None else value
        for line in basket.all_lines():
            product = line.product
            if self.range.contains_product(product) and line.product.has_stockrecord:
                price = getattr(product.stockrecord, self.price_field)
                if not price:
                    continue
                quantity_to_consume = min(line.quantity_without_discount,
                                          int(((value - value_of_matches)/price).quantize(Decimal(1),
                                                                                              ROUND_UP)))
                value_of_matches += price * quantity_to_consume
                line.consume(quantity_to_consume)
                consumed_products.extend((line.product,)*int(quantity_to_consume))
            if value_of_matches >= value:
                break
        return consumed_products

# ========
# Benefits
# ========

class PercentageDiscountBenefit(Benefit):
    """
    An offer benefit that gives a percentage discount
    """

    class Meta:
        proxy = True

    def apply(self, basket, condition=None):
        discount = Decimal('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()
        
        for line in basket.all_lines():
            if affected_items >= max_affected_items:
                break
            product = line.product
            if self.range.contains_product(product) and product.has_stockrecord:
                price = getattr(product.stockrecord, self.price_field)
                quantity = min(line.quantity_without_discount, 
                               max_affected_items - affected_items)
                line_discount = self.round(self.value/100 * price * int(quantity))
                line.discount(line_discount, quantity)
                affected_items += quantity
                discount += line_discount
                
        if discount > 0 and condition:
            condition.consume_items(basket)
        return discount


class AbsoluteDiscountBenefit(Benefit):
    """
    An offer benefit that gives an absolute discount
    """

    class Meta:
        proxy = True

    def apply(self, basket, condition=None):
        discount = Decimal('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()
        
        for line in basket.all_lines():
            if affected_items >= max_affected_items:
                break
            product = line.product
            if self.range.contains_product(product) and product.has_stockrecord:
                price = getattr(product.stockrecord, self.price_field)
                if not price:
                    # Avoid zero price products
                    continue
                remaining_discount = self.value - discount
                quantity_affected = int(min(line.quantity_without_discount, 
                                        max_affected_items - affected_items,
                                        math.ceil(remaining_discount / price)))
                
                # Update line with discounts
                line_discount = self.round(min(remaining_discount, quantity_affected * price))
                line.discount(line_discount, quantity_affected)
                
                # Update loop vars
                affected_items += quantity_affected
                remaining_discount -= line_discount
                discount += line_discount
        if discount > 0 and condition:
            condition.consume_items(basket)
            
        return discount


class FixedPriceBenefit(Benefit):
    """
    An offer benefit that gives the items in the condition for a 
    fixed price.  This is useful for "bundle" offers.
    
    Note that we ignore the benefit range here and only give a fixed price
    for the products in the condition range.
    
    The condition should be a count condition
    """
    class Meta:
        proxy = True

    def apply(self, basket, condition=None):
        num_covered = 0
        num_permitted = int(condition.value)
        covered_lines = []
        product_total = Decimal('0.00')
        for line in basket.all_lines():
            product = line.product
            if condition.range.contains_product(product) and line.quantity_without_discount > 0:
                # Line is available - determine quantity to consume and 
                # record the total of the consumed products
                if isinstance(condition, CoverageCondition):
                    quantity = 1
                else:
                    quantity = min(line.quantity_without_discount, num_permitted - num_covered)
                num_covered += quantity
                product_total += quantity*line.unit_price_incl_tax
                covered_lines.append((line, quantity))
            if num_covered >= num_permitted:
                break
        discount = max(product_total - self.value, Decimal('0.00'))
        
        if not discount:
            return discount
        
        # Apply discount weighted by original value of line
        discount_applied = Decimal('0.00')
        last_line = covered_lines[-1][0]
        for line, quantity in covered_lines:
            if line == last_line:
                # If last line, we just take the difference to ensure that
                # a rounding doesn't lead to an off-by-one error
                line_discount = discount - discount_applied
            else:
                line_discount = self.round(discount * (line.unit_price_incl_tax * quantity) / product_total)
            line.discount(line_discount, quantity)
            discount_applied += line_discount
        return discount 
        
        # Apply discount weighted by original value of line
        for line, quantity in covered_lines:
            line_discount = self.round(discount * (line.unit_price_incl_tax * quantity) / product_total)  
            line.discount(line_discount.quantize(Decimal('.01')), quantity)
        return discount 


class MultibuyDiscountBenefit(Benefit):
    class Meta:
        proxy = True

    def apply(self, basket, condition=None):
        benefit_lines = [line for line in basket.all_lines() if (self.range.contains_product(line.product) and
                                                                 line.quantity_without_discount > 0 and
                                                                 line.product.has_stockrecord)]
        if not benefit_lines:
            return self.round(Decimal('0.00'))

        # Determine cheapest line to give for free
        line_price_getter = lambda line: getattr(line.product.stockrecord,
                                                 self.price_field)
        free_line = min(benefit_lines, key=line_price_getter)
        discount = line_price_getter(free_line)

        if condition:
            compare = lambda l1, l2: cmp(line_price_getter(l2),
                                         line_price_getter(l1))
            lines_with_price = [line for line in basket.all_lines() if line.product.has_stockrecord]
            sorted_lines = sorted(lines_with_price, compare)
            free_line.discount(discount, 1)
            if condition.range.contains_product(line.product):
                condition.consume_items(basket, lines=sorted_lines,
                                        value=condition.value-1)
            else:
                condition.consume_items(basket, lines=sorted_lines)
        else:
            free_line.discount(discount, 0)
        return self.round(discount)


# We need to import receivers at the bottom of this script
from oscar.apps.offer.receivers import receive_basket_voucher_change
