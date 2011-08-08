from decimal import Decimal

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.conf import settings


class Transaction(models.Model):
    """
    A transaction for payment sources which need a secondary 'transaction' to actually take the money
    
    This applies mainly to credit card sources which can be a pre-auth for the money.  A 'complete'
    needs to be run later to debit the money from the account.
    """
    source = models.ForeignKey('payment.Source', related_name='transactions')
    
    # We define some sample types
    DEBIT, REFUND = 'Debit', 'Refund'
    txn_type = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    reference = models.CharField(max_length=128, null=True)
    status = models.CharField(max_length=128, null=True)
    date_created = models.DateField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s of %.2f" % (self.txn_type, self.amount)


class AbstractSource(models.Model):
    """
    A source of payment for an order.  
    
    This is normally a credit card which has been pre-authed for the order
    amount, but some applications will allow orders to be paid for using
    multiple sources such as cheque, credit accounts, gift cards.  Each payment
    source will have its own entry.
    """
    order = models.ForeignKey('order.Order', related_name='sources')
    source_type = models.ForeignKey('payment.SourceType')
    currency = models.CharField(max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY)
    amount_allocated = models.DecimalField(decimal_places=2, max_digits=12)
    amount_debited = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    amount_refunded = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    reference = models.CharField(max_length=128, blank=True, null=True)
    
    # A dictionary of submission data that is stored as part of the
    # checkout process.
    submission_data = {}
    
    class Meta:
        abstract = True

    def __unicode__(self):
        description = "Allocation of %.2f from type %s" % (self.amount_allocated, self.source_type)
        if self.reference:
            description += " (reference: %s)" % self.reference
        return description
    
    def balance(self):
        return self.amount_allocated - self.amount_debited + self.amount_refunded
    
    def debit(self, amount=None, reference=None, status=None):
        """
        Convenience method for recording debits against this source
        """
        if amount is None:
            amount = self.balance()
        self.amount_debited += amount
        self.save()
        Transaction.objects.create(source=self,
                                   txn_type=Transaction.DEBIT,
                                   amount=amount,
                                   reference=reference,
                                   status=status)
        
    def refund(self, amount, reference=None, status=None):
        """
        Convenience method for recording refunds against this source
        """
        self.amount_refunded += amount
        self.save()
        Transaction.objects.create(source=self,
                                   txn_type=Transaction.REFUND,
                                   amount=amount,
                                   reference=reference,
                                   status=status)
    
    @property
    def amount_available_for_refund(self):
        """
        Return the amount available to be refunded
        """
        return self.amount_debited - self.amount_refunded
    
    
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
