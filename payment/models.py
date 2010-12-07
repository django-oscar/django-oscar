from django.db import models


class PaymentSource(models.Model):
    order = models.ForeignKey('core.Order', related_name='payment_sources')
    type = models.CharField(max_length=128)
    initial_amount = models.IntegerField()
    balance = models.IntegerField()
    reference = models.CharField(max_length=128, blank=True, null=True)
    
    def __unicode__(self):
        description = "Payment of %.2f from %s" % (self.initial_amount, self.type)
        if self.reference:
            description += " (reference: %s)" % self.reference
        return description
    
    
class PaymentSourceTransaction(models.Model):
    source = models.ForeignKey('payment.PaymentSource', related_name='transactions')
    type = models.CharField(max_length=128, blank=True)
    delta_amount = models.FloatField()
    reference = models.CharField(max_length=128)
    transaction_date = models.DateField()
    
    def __unicode__(self):
        return "Transaction of %.2f" % self.delta_amount
