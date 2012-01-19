from django.db import models
from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping.abstract_models import AbstractOrderAndItemLevelChargeMethod


class OrderAndItemLevelChargeMethod(AbstractOrderAndItemLevelChargeMethod):
    pass


class WeightBand(models.Model):
    upper_limit = models.DecimalField(decimal_places=2, max_digits=12,
                                      help_text=_("""Enter upper limit of this weight band in Kg"""))
    charge = models.DecimalField(decimal_places=2, max_digits=12)
    
    @property
    def weight_from(self):
        lower_bands = WeightBand.objects.filter(upper_limit__lt=self.upper_limit).order_by('-upper_limit')
        if not lower_bands:
            return D('0.00')
        return lower_bands[0].upper_limit
    
    @property
    def weight_to(self):
        return self.upper_limit
    
    class Meta:
        ordering = ['upper_limit']

    def __unicode__(self):
        return u'Charge for weights up to %s' % (self.upper_limit,)
        
    @classmethod
    def get_band_for_weight(cls, weight):
        """
        Return the weight band for a given weight
        """
        bands = WeightBand.objects.filter(upper_limit__gte=weight).order_by('upper_limit')
        if not bands.count():
            # No band for this weight
            return None
        return bands[0]