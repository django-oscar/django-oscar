"""
Core address objects
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractAddress(models.Model):
    """
    Core address object
    
    This is normally subclassed and extended to provide models for 
    delivery and billing addresses.
    """
    # @todo: Need a way of making these choice lists configurable 
    # per project
    MR, MISS, MRS, MS, DR = ('Dr', 'Miss', 'Mrs', 'Ms', 'Dr')
    TITLE_CHOICES = (
        (MR, _("Mr")),
        (MISS, _("Miss")),
        (MRS, _("Mrs")),
        (MS, _("Ms")),
        (DR, _("Dr")),
    )
    # User is optional as this address could belong to an anonymous customer
    user = models.ForeignKey('auth.User', null=True, blank=True)
    title = models.CharField(_("Title"), max_length=64, choices=TITLE_CHOICES, blank=True)
    first_name = models.CharField(_("First name"), max_length=255, blank=True)
    last_name = models.CharField(_("Last name"), max_length=255)
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True)
    line3 = models.CharField(_("City"), max_length=255, blank=True)
    line4 = models.CharField(_("State/County"), max_length=255, blank=True)
    postcode = models.CharField(_("Post/Zip-code"), max_length=64)
    # @todo: Create a country model to use as a foreign key
    country = models.CharField(_("Country"), max_length=255, blank=True)
    
    class Meta:
        abstract = True
        
    def get_salutation(self):
        """
        Returns the salutation
        """
        return " ".join([part for part in [self.title, self.first_name, self.last_name] if part])
        
    def __unicode__(self):
        parts = (self.get_salutation(), self.line1, self.line2, self.line3, self.line4,
                 self.postcode, self.country)
        return u", ".join([part for part in parts if part])


class AbstractDeliveryAddress(AbstractAddress):
    """
    Delivery address 
    """
    phone_number = models.CharField(max_length=32, blank=True, null=True)
    notes = models.TextField(blank=True, null=True) 
    
    class Meta:
        abstract = True
        verbose_name_plural = "Delivery addresses"


class AbstractBillingAddress(AbstractAddress):
    """
    Billing address
    """
    class Meta:
        abstract = True
        verbose_name_plural = "Billing addresses"    
