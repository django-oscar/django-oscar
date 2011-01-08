from django.db import models
from django.utils.translation import ugettext_lazy as _

class AbstractAddress(models.Model):
    """
    Core address object
    
    This is normally subclassed and extended to provide models for 
    delivery and billing addresses.
    """
    MR, MISS, MRS, MS, DR = ('Dr', 'Miss', 'Mrs', 'Ms', 'Dr')
    TITLE_CHOICES = (
        (MR, _("Mr")),
        (MISS, _("Miss")),
        (MRS, _("Mrs")),
        (MS, _("Ms")),
        (DR, _("Dr")),
    )
    title = models.CharField(max_length=64, choices=TITLE_CHOICES, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, null=True)
    line3 = models.CharField(max_length=255, blank=True, null=True)
    line4 = models.CharField(max_length=255, blank=True, null=True)
    postcode = models.CharField(max_length=64)
    # @todo: Create a country model to use as a foreign key
    country = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        abstract = True
        
    def get_salutation(self):
        return "%s %s %s" % (self.title, self.first_name, self.last_name)    
        
    def __unicode__(self):
        parts = (self.get_salutation(), self.line1, self.line2, self.line3, self.line4,
                 self.postcode, self.country)
        return ", ".join([part for part in parts if part])
