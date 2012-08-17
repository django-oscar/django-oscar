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
    AUTHORISE, DEBIT, REFUND = 'Authorise', 'Debit', 'Refund'
    txn_type = models.CharField(_('Type'), max_length=128, blank=True)
    amount = models.DecimalField(_('Amount'), decimal_places=2, max_digits=12)
    reference = models.CharField(_('Reference'), max_length=128, null=True)
    status = models.CharField(_('Status'), max_length=128, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return _("%(type)s of %(amount).2f") % {'type': self.txn_type, 'amount': self.amount}

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class Source(models.Model):
    """
    A source of payment for an order.  
    
    This is normally a credit card which has been pre-authed for the order
    amount, but some applications will allow orders to be paid for using
    multiple sources such as cheque, credit accounts, gift cards.  Each payment
    source will have its own entry.
    """
    order = models.ForeignKey('order.Order', related_name='sources')
    source_type = models.ForeignKey('payment.SourceType')
    currency = models.CharField(_('Currency'), max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY)
    
    # Track the various amounts associated with this source
    amount_allocated = models.DecimalField(_('Amount Allocated'), decimal_places=2, max_digits=12, default=Decimal('0.00'))
    amount_debited = models.DecimalField(_('Amount Debited'), decimal_places=2, max_digits=12, default=Decimal('0.00'))
    amount_refunded = models.DecimalField(_('Amount Refunded'), decimal_places=2, max_digits=12, default=Decimal('0.00'))
    
    # Reference number for this payment source.  This is often used to look up a
    # transaction model for a particular payment partner. 
    reference = models.CharField(_('Reference'), max_length=128, blank=True, null=True)
    
    # A customer-friendly label for the source, eg XXXX-XXXX-XXXX-1234
    label = models.CharField(_('Label'), max_length=128, blank=True, null=True)
    
    # A dictionary of submission data that is stored as part of the
    # checkout process.
    submission_data = None
    
    # We keep a list of deferred transactions that are only actually saved when 
    # the source is saved for the first time
    deferred_txns = None

    class Meta:
        verbose_name = _("Source")
        verbose_name_plural = _("Sources")

    def __unicode__(self):
        description = _("Allocation of %(amount).2f from type %(type)s") % {
            'amount': self.amount_allocated, 'type': self.source_type}
        if self.reference:
            description += _(" (reference: %s)") % self.reference
        return description
    
    def save(self, *args, **kwargs):
        super(Source, self).save(*args, **kwargs)
        if self.deferred_txns:
            for txn in self.deferred_txns:
                self._create_transaction(*txn)
    
    def balance(self):
        return self.amount_allocated - self.amount_debited + self.amount_refunded
    
    def create_deferred_transaction(self, txn_type, amount, reference=None, status=None):
        """
        Register the data for a transaction that can't be created yet due to FK
        constraints.  This happens at checkout where create an payment source and a
        transaction but can't save them until the order model exists.
        """
        if self.deferred_txns is None:
            self.deferred_txns = []
        self.deferred_txns.append((txn_type, amount, reference, status))
    
    def _create_transaction(self, txn_type, amount, reference=None, status=None):
        Transaction.objects.create(source=self,
                                   txn_type=txn_type,
                                   amount=amount,
                                   reference=reference,
                                   status=status)
    
    def allocate(self, amount, reference=None, status=None):
        """
        Convenience method for ring-fencing money against this source
        """
        self.amount_allocated += amount
        self.save()
        self._create_transaction(Transaction.AUTHORISE, amount, reference, status)
    
    def debit(self, amount=None, reference=None, status=None):
        """
        Convenience method for recording debits against this source
        """
        if amount is None:
            amount = self.balance()
        self.amount_debited += amount
        self.save()
        self._create_transaction(Transaction.DEBIT, amount, reference, status)
        
    def refund(self, amount, reference=None, status=None):
        """
        Convenience method for recording refunds against this source
        """
        self.amount_refunded += amount
        self.save()
        self._create_transaction(Transaction.REFUND, amount, reference, status)
    
    @property
    def amount_available_for_refund(self):
        """
        Return the amount available to be refunded
        """
        return self.amount_debited - self.amount_refunded
    
    
class SourceType(models.Model):
    """
    A type of payment source.
    
    This could be an external partner like PayPal or DataCash,
    or an internal source such as a managed account.i
    """
    name = models.CharField(_('Name'), max_length=128)
    code = models.SlugField(_('Code'), max_length=128, help_text=_("""This is used within
        forms to identify this source type"""))

    class Meta:
        verbose_name = _("Source Type")
        verbose_name_plural = _("Source Types")

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(SourceType, self).save(*args, **kwargs)
    

class Bankcard(models.Model):
    user = models.ForeignKey('auth.User', related_name='bankcards')
    card_type = models.CharField(_('Card Type'), max_length=128)
    name = models.CharField(_('Name'), max_length=255)
    number = models.CharField(_('Number'), max_length=32)
    expiry_date = models.DateField(_('Expiry Date'))
    
    # For payment partners who are storing the full card details for us
    partner_reference = models.CharField(_('Partner Reference'), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _("Bankcard")
        verbose_name_plural = _("Bankcards")

    def save(self, *args, **kwargs):
        self.number = self._get_obfuscated_number()
        super(Bankcard, self).save(*args, **kwargs)    
        
    def _get_obfuscated_number(self):
        return u"XXXX-XXXX-XXXX-%s" % self.number[-4:]
