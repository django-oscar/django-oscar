from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext as _


class AbstractDiscountOffer(models.Model):
    u"""
    A fixed-discount offer (eg get 10% off all fiction books)
    """
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    products = models.ManyToManyField('product.Item')
    
    ABSOLUTE_DISCOUNT, PERCENTAGE_DISCOUNT, FINAL_PRICE = "Absolute", "Percentage", "Final price"
    TYPE_CHOICES = (
        (ABSOLUTE_DISCOUNT, _("An absolute amount of discount off the site price")),
        (PERCENTAGE_DISCOUNT, _("A percentage discount off the site price")),
        (FINAL_PRICE, _("Sets the site price")),
    )
    discount_type = models.CharField(_("Discount type"), max_length=128, choices=TYPE_CHOICES, default=PERCENTAGE_DISCOUNT)
    discount_value = models.DecimalField(decimal_places=2, max_digits=12, 
        help_text="""For percentage values, enter integers less than 100 (eg '25' for a 25% discount)""")
    
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_created']
        abstract = True
        
    def __unicode__(self):
        return self.name    
        
    def is_active(self, test_date=None):
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date

    def num_products(self):
        return self.products.count()

    def apply(self):
        u"""
        Applies this offer to its linked products.
        
        The default behaviour of this method is to always
        apply this offer, even if it makes the product more expensive.
        This behaviour can of course customised by subclassing.
        """
        for product in self.products.all():
            self._apply_discount_to_product(product)
            
    def _apply_discount_to_product(self, product):
        u"""
        Applies this offer to an individual product
        """
        if product.has_stockrecord:
            discount_price = self._get_discount_price(product)
            product.stockrecord.set_discount_price(discount_price)
    
    def _get_discount_price(self, product):
        u"""
        Returns the discounted price
        """
        current_price = product.stockrecord.price_excl_tax
        if self.discount_type == self.ABSOLUTE_DISCOUNT:
            return max(Decimal('0.00'), current_price - self.discount_value)
        elif self.discount_type == self.PERCENTAGE_DISCOUNT:
            return current_price * (1 - self.discount_value) / 100
        return self.discount_value 
                

        
        
