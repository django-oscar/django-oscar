from decimal import Decimal

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.conf import settings


class AbstractSource(models.Model):
    """
    A source of payment for an order.  
    
    This is normally a credit card which has been pre-authed for the order
    amount, but some applications will allow orders to be paid for using
    multiple sources such as cheque, credit accounts, gift cards.  Each payment
    source will have its own entry.
    """
    order = models.ForeignKey('order.Order', related_name='sources')
    type = models.ForeignKey('payment.SourceType')
    currency = models.CharField(max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY)
    amount_allocated = models.DecimalField(decimal_places=2, max_digits=12)
    amount_debited = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    reference = models.CharField(max_length=128, blank=True, null=True)
    
    # A dictionary of submission data that is stored as part of the
    # checkout process.
    submission_data = {}
    
    class Meta:
        abstract = True

    def __unicode__(self):
        description = "Allocation of %.2f from type %s" % (self.amount_allocated, self.type)
        if self.reference:
            description += " (reference: %s)" % self.reference
        return description
    
    def balance(self):
        return self.amount_allocated - self.amount_debited
    
    
class AbstractSourceType(models.Model):
    """
    A type of payment source.
    
    This could be an external partner like PayPal or DataCash,
    or an internal source such as a managed account.i
    """
    name = models.CharField(max_length=128)
    code = models.SlugField(max_length=128, help_text=_("""This is used within
        forms to identify this source type"""))

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractSourceType, self).save(*args, **kwargs)
    

class AbstractTransaction(models.Model):
    """
    A transaction for payment sources which need a secondary 'transaction' to actually take the money
    
    This applies mainly to credit card sources which can be a pre-auth for the money.  A 'complete'
    needs to be run later to debit the money from the account.
    """
    source = models.ForeignKey('payment.Source', related_name='transactions')
    type = models.CharField(max_length=128, blank=True)
    delta_amount = models.FloatField()
    reference = models.CharField(max_length=128)
    date_created = models.DateField()
    
    class Meta:
        abstract = True

    def __unicode__(self):
        return "Transaction of %.2f" % self.delta_amount


class AbstractBankcard(models.Model):
    user = models.ForeignKey('auth.User', related_name='bankcards')
    card_type = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=32)
    expiry_date = models.DateField()
    
    # For payment partners who are storing the full card details for us
    partner_reference = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        self.number = self._get_obfuscated_number()
        super(AbstractBankcard, self).save(*args, **kwargs)    
        
    def _get_obfuscated_number(self):
        return u"XXXX-XXXX-XXXX-%s" % self.number[-4:]
