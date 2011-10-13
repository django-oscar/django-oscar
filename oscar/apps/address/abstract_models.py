import zlib

from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractAddress(models.Model):
    """
    Superclass address object

    This is subclassed and extended to provide models for 
    user, shipping and billing addresses.

    The only required fields are last_name, line1 and postcode.
    """
    # @todo: Need a way of making these choice lists configurable 
    # per project
    MR, MISS, MRS, MS, DR = ('Mr', 'Miss', 'Mrs', 'Ms', 'Dr')
    TITLE_CHOICES = (
        (MR, _("Mr")),
        (MISS, _("Miss")),
        (MRS, _("Mrs")),
        (MS, _("Ms")),
        (DR, _("Dr")),
    )
    title = models.CharField(_("Title"), max_length=64, choices=TITLE_CHOICES, blank=True, null=True)
    first_name = models.CharField(_("First name"), max_length=255, blank=True, null=True)
    last_name = models.CharField(_("Last name"), max_length=255, blank=True)
    
    # We use quite a few lines of an address as they are often quite long and 
    # it's easier to just hide the unnecessary ones than add extra ones.
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True, null=True)
    line3 = models.CharField(_("Third line of address"), max_length=255, blank=True, null=True)
    line4 = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State/County"), max_length=255, blank=True, null=True)
    postcode = models.CharField(_("Post/Zip-code"), max_length=64)
    country = models.ForeignKey('address.Country')
    
    # A field only used for searching addresses - this contains all the relevant fields
    search_text = models.CharField(_("Search text"), max_length=1000)
    
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self._clean_fields()
        self._update_search_text()
        super(AbstractAddress, self).save(*args, **kwargs)
        
    @property    
    def city(self):
        return self.line4     
        
    def _clean_fields(self):
        """
        Clean up fields
        """
        for field in ['first_name', 'last_name', 'line1', 'line2', 'line3', 'line4', 'postcode']:
            if self.__dict__[field]:
               self.__dict__[field] = self.__dict__[field].strip()
        
        # Ensure postcodes are always uppercase
        if self.postcode:
            self.postcode = self.postcode.upper()
            
    def _update_search_text(self):
        search_fields = filter(lambda x: x, [self.first_name, self.last_name, 
                                             self.line1, self.line2, self.line3, self.line4, self.state,
                                             self.postcode, self.country.name]) 
        self.search_text = ' '.join(search_fields) 
        
    @property    
    def summary(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        return u", ".join(self.active_address_fields())    
        
    def populate_alternative_model(self, address_model):
        """
        For populating an address model using the matching fields
        from this one.
        
        This is used to convert a user address to a shipping address
        as part of the checkout process.
        """
        destination_field_names = [field.name for field in address_model._meta.fields]
        for field_name in [field.name for field in self._meta.fields]:
            if field_name in destination_field_names and field_name != 'id':
                setattr(address_model, field_name, getattr(self, field_name))
                
    def active_address_fields(self):
        u"""
        Returns the non-empty components of the address, but merging the
        title, first_name and last_name into a single line.
        """
        self._clean_fields()
        fields = filter(lambda x: x, [self.salutation(), self.line1, self.line2, self.line3,
                                      self.line4, self.state, self.postcode])
        if self.country:
            fields.append(self.country.name)
        return fields
        
    def salutation(self):
        u"""Returns the salutation"""
        return u" ".join([part for part in [self.title, self.first_name, self.last_name] if part])
        
    def name(self):
        """
        Returns the full name
        """
        return u" ".join([part for part in [self.first_name, self.last_name] if part])    
        
    def __unicode__(self):
        return self.summary


class AbstractCountry(models.Model):
    """
    International Organization for Standardization (ISO) 3166-1 Country list.
    """
    iso_3166_1_a2 = models.CharField(_('ISO 3166-1 alpha-2'), max_length=2, primary_key=True)
    iso_3166_1_a3 = models.CharField(_('ISO 3166-1 alpha-3'), max_length=3, null=True, db_index=True)
    iso_3166_1_numeric = models.PositiveSmallIntegerField(_('ISO 3166-1 numeric'), null=True, db_index=True)
    name = models.CharField(_('Official name (CAPS)'), max_length=128)
    printable_name = models.CharField(_('Country name'), max_length=128)
    
    is_highlighted = models.BooleanField(default=False, db_index=True)
    is_shipping_country = models.BooleanField(default=False, db_index=True)
    
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
    notes = models.TextField(blank=True, null=True, help_text="""Shipping notes""")
    
    class Meta:
        abstract = True
        verbose_name_plural = "shipping addresses"
        
    @property    
    def order(self):
        """
        Return the order linked to this shipping address
        """
        orders = self.order_set.all()
        if not orders:
            return None
        return orders[0]
        
        
class AbstractUserAddress(AbstractShippingAddress):
    """
    A user address which forms an "AddressBook" for a user.
    
    We use a separate model to shipping and billing (even though there will be
    some data duplication) because we don't want shipping/billing addresses changed
    or deleted once an order has been placed.  By having a separate model, we allow
    users the ability to add/edit/delete from their address book without affecting
    orders already placed. 
    """
    user = models.ForeignKey('auth.User', related_name='addresses')
    
    # Customers can set defaults
    is_default_for_shipping = models.BooleanField(default=False)
    is_default_for_billing = models.BooleanField(default=False)
    
    # We keep track of the number of times an address has been used
    # as a shipping address so we can show the most popular ones 
    # first at the checkout.
    num_orders = models.PositiveIntegerField(default=0)
    
    # A hash is kept to try and avoid duplicate addresses being added
    # to the address book.
    hash = models.CharField(max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def generate_hash(self):
        u"""Returns a hash of the address summary."""
        # We use an upper-case version of the summary
        return zlib.crc32(self.summary.strip().upper().encode('UTF8'))

    def save(self, *args, **kwargs):
        u"""Save a hash of the address fields"""
        # Save a hash of the address fields so we can check whether two 
        # addresses are the same to avoid saving duplicates
        self.hash = self.generate_hash()
        super(AbstractUserAddress, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        verbose_name_plural = "User addresses"
        ordering = ['-num_orders']


class AbstractBillingAddress(AbstractAddress):
    
    class Meta:
        abstract = True
        verbose_name_plural = "Billing addresses"   
        
    @property    
    def order(self):
        """
        Return the order linked to this shipping address
        """
        orders = self.order_set.all()
        if not orders:
            return None
        return orders[0] 
