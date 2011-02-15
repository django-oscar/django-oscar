"""
Core address objects
"""
import zlib

from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractAddress(models.Model):
    u"""
    Superclass address object
    
    This is subclassed and extended to provide models for 
    user, shipping and billing addresses.
    
    The only required fields are last_name, line1 and postcode.
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
    title = models.CharField(_("Title"), max_length=64, choices=TITLE_CHOICES, blank=True)
    first_name = models.CharField(_("First name"), max_length=255, blank=True)
    last_name = models.CharField(_("Last name"), max_length=255)
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True)
    line3 = models.CharField(_("City"), max_length=255, blank=True)
    line4 = models.CharField(_("State/County"), max_length=255, blank=True)
    postcode = models.CharField(_("Post/Zip-code"), max_length=64)
    country = models.ForeignKey('address.Country')
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        self._clean_fields()
        super(AbstractAddress, self).save(*args, **kwargs)    
        
    def _clean_fields(self):
        # Ensure fields are stripped 
        self.first_name = self.first_name.strip()
        for field in ['first_name', 'last_name', 'line1', 'line2', 'line3', 'line4', 'postcode']:
            self.__dict__[field] = self.__dict__[field].strip()
        
        # Ensure postcodes are always uppercase
        if self.postcode:
            self.postcode = self.postcode.upper()    
        
    @property    
    def summary(self):
        u"""
        Returns a single string summary of the address,
        separating fields using commas.
        """
        return u", ".join(self.active_address_fields())    
        
    def populate_alternative_model(self, address_model):
        u"""
        For populating an address model using the matching fields
        from this one.
        
        This is used to convert a user address to a shipping address
        as part of the checkout process.
        """
        destination_field_names = list(address_model._meta.get_all_field_names())
        for field_name in self._meta.get_all_field_names():
            if field_name in destination_field_names and field_name != 'id':
                setattr(address_model, field_name, getattr(self, field_name))
                
    def active_address_fields(self):
        u"""
        Returns the non-empty components of the address, but merging the
        title, first_name and last_name into a single line.
        """
        self._clean_fields()
        return filter(lambda x: x, [self.salutation(), self.line1, self.line2, self.line3,
                                    self.line4, self.postcode, self.country.name])
        
    def salutation(self):
        """
        Returns the salutation
        """
        return " ".join([part for part in [self.title, self.first_name, self.last_name] if part])
        
    def __unicode__(self):
        return self.summary


class AbstractCountry(models.Model):
    u"""
    International Organization for Standardization (ISO) 3166-1 Country list
    """
    iso_3166_1_a2 = models.CharField(_('ISO 3166-1 alpha-2'), max_length=2, primary_key=True)
    iso_3166_1_a3 = models.CharField(_('ISO 3166-1 alpha-3'), max_length=3, null=True)
    iso_3166_1_numeric = models.PositiveSmallIntegerField(_('ISO 3166-1 numeric'), null=True)
    name = models.CharField(_('Official name (CAPS)'), max_length=128)
    printable_name = models.CharField(_('Country name'), max_length=128)
    
    is_highlighted = models.BooleanField(default=False)
    is_shipping_country = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ('-is_highlighted', 'name',)
            
    def __unicode__(self):
        return self.printable_name
        

class AbstractShippingAddress(AbstractAddress):
    u"""
    Shipping address.
    
    A shipping address should not be edited once the order has been placed - 
    it should be read-only after that. 
    """
    phone_number = models.CharField(max_length=32, blank=True, null=True)
    notes = models.TextField(blank=True, null=True) 
    
    class Meta:
        abstract = True
        verbose_name_plural = "shipping addresses"
        
        
class AbstractUserAddress(AbstractShippingAddress):
    u"""
    A user address which forms an "AddressBook" for a user.
    
    We use a separate model to shipping and billing (even though there will be
    some data duplication) because we don't want shipping/billing addresses changed
    or deleted once an order has been placed.  By having a separate model, we allow
    users the ability to add/edit/delete from their address book without affecting
    orders already placed. 
    """
    user = models.ForeignKey('auth.User', related_name='addresses')
    
    # We keep track of the number of times an address has been used
    # as a shipping address so we can show the most popular ones 
    # first at the checkout.
    num_orders = models.PositiveIntegerField(default=0)
    # A hash is kept to try and avoid duplicate addresses being added
    # to the address book.
    hash = models.CharField(max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def generate_hash(self):
        u"""
        Returns a hash of the address summary.
        """
        # We use an upper-case version of the summary
        return zlib.crc32(self.summary.strip().upper())

    def save(self, *args, **kwargs):
        # Save a hash of the address fields so we can check whether two 
        # addresses are the same to avoid saving duplicates
        self.hash = self.generate_hash()
        super(AbstractUserAddress, self).save(*args, **kwargs)  
    
    class Meta:
        abstract = True
        verbose_name_plural = "User addresses"
        ordering = ['-num_orders']


class AbstractBillingAddress(AbstractAddress):
    u"""
    Billing address
    """
    class Meta:
        abstract = True
        verbose_name_plural = "Billing addresses"    
