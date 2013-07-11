import re
import zlib

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core import exceptions

from oscar.core.compat import AUTH_USER_MODEL


class AbstractAddress(models.Model):
    """
    Superclass address object

    This is subclassed and extended to provide models for
    user, shipping and billing addresses.
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

    # Regex for each country. Not listed countries don't use postcodes
    # Based on http://en.wikipedia.org/wiki/List_of_postal_codes
    POSTCODES_REGEX = {
        'AC': R'^[A-Z]{4}[0-9][A-Z]$',
        'AD': R'^AD[0-9]{3}$',
        'AF': R'^[0-9]{4}$',
        'AI': R'^AI-2640$',
        'AL': R'^[0-9]{4}$',
        'AM': R'^[0-9]{4}$',
        'AR': R'^([0-9]{4}|[A-Z][0-9]{4}[A-Z]{3}$',
        'AS': R'^[0-9]{5}(-[0-9]{4}|-[0-9]{6})?$',
        'AT': R'^[0-9]{4}$',
        'AU': R'^[0-9]{4}$',
        'AX': R'^[0-9]{5}$',
        'AZ': R'^AZ[0-9]{4}$',
        'BA': R'^[0-9]{5}$',
        'BB': R'^BB[0-9]{5}$',
        'BD': R'^[0-9]{4}$',
        'BE': R'^[0-9]{4}$',
        'BG': R'^[0-9]{4}$',
        'BH': R'^[0-9]{3,4}$',
        'BL': R'^[0-9]{5}$',
        'BM': R'^[A-Z]{2}([0-9]{2}|[A-Z]{2})',
        'BN': R'^[A-Z}{2}[0-9]]{4}$',
        'BO': R'^[0-9]{4}$',
        'BR': R'^[0-9]{5}(-[0-9]{3})?$',
        'BT': R'^[0-9]{3}$',
        'BY': R'^[0-9]{6}$',
        'CA': R'^[A-Z][0-9][A-Z][0-9][A-Z][0-9]$',
        'CC': R'^[0-9]{4}$',
        'CH': R'^[0-9]{4}$',
        'CL': R'^([0-9]{7}|[0-9]{3}-[0-9]{4})$',
        'CN': R'^[0-9]{6}$',
        'CO': R'^[0-9]{6}$',
        'CR': R'^[0-9]{4,5}$',
        'CU': R'^[0-9]{5}$',
        'CV': R'^[0-9]{4}$',
        'CX': R'^[0-9]{4}$',
        'CY': R'^[0-9]{4}$',
        'CZ': R'^[0-9]{5}$',
        'DE': R'^[0-9]{5}$',
        'DK': R'^[0-9]{4}$',
        'DO': R'^[0-9]{5}$',
        'DZ': R'^[0-9]{5}$',
        'EC': R'^EC[0-9]{6}$',
        'EE': R'^[0-9]{5}$',
        'EG': R'^[0-9]{5}$',
        'ES': R'^[0-9]{5}$',
        'ET': R'^[0-9]{4}$',
        'FI': R'^[0-9]{5}$',
        'FK': R'^[A-Z]{4}[0-9][A-Z]{2}$',
        'FM': R'^[0-9]{5}(-[0-9]{4})?$',
        'FO': R'^[0-9]{3}$',
        'FR': R'^[0-9]{5}$',
        'GA': R'^[0-9]{2}.*[0-9]{2}$',
        'GB': R'^[A-Z][A-Z0-9]{1,3}[0-9][A-Z]{2}$',
        'GE': R'^[0-9]{4}$',
        'GF': R'^[0-9]{5}$',
        'GG': R'^([A-Z]{2}[0-9]{2,3}[A-Z]{2}$',
        'GI': R'^GX111AA$',
        'GL': R'^[0-9]{4}$',
        'GP': R'^[0-9]{5}$',
        'GR': R'^[0-9]{5}$',
        'GS': R'^SIQQ1ZZ$',
        'GT': R'^[0-9]{5}$',
        'GU': R'^[0-9]{5}$',
        'GW': R'^[0-9]{4}$',
        'HM': R'^[0-9]{4}$',
        'HN': R'^[0-9]{5}$',
        'HR': R'^[0-9]{5}$',
        'HT': R'^[0-9]{4}$',
        'HU': R'^[0-9]{4}$',
        'ID': R'^[0-9]{5}$',
        'IL': R'^[0-9]{7}$',
        'IM': R'^IM[0-9]{2,3}[A-Z]{2}$$',
        'IN': R'^[0-9]{6}$',
        'IO': R'^[A-Z]{4}[0-9][A-Z]{2}$',
        'IQ': R'^[0-9]{5}$',
        'IR': R'^[0-9]{5}-[0-9]{5}$',
        'IS': R'^[0-9]{3}$',
        'IT': R'^[0-9]{5}$',
        'JE': R'^JE[0-9]{2}[A-Z]{2}$',
        'JM': R'^JM[A-Z]{3}[0-9]{2}$',
        'JO': R'^[0-9]{5}$',
        'JP': R'^[0-9]{3}-?[0-9]{4}$',
        'KE': R'^[0-9]{5}$',
        'KG': R'^[0-9]{6}$',
        'KH': R'^[0-9]{5}$',
        'KR': R'^[0-9]{3}-?[0-9]{3}$',
        'KY': R'^KY[0-9]-[0-9]{4}$',
        'KZ': R'^[0-9]{6}$',
        'LA': R'^[0-9]{5}$',
        'LB': R'^[0-9]{8}$',
        'LI': R'^[0-9]{4}$',
        'LK': R'^[0-9]{5}$',
        'LR': R'^[0-9]{4}$',
        'LS': R'^[0-9]{3}$',
        'LT': R'^[0-9]{5}$',
        'LU': R'^[0-9]{4}$',
        'LV': R'^LV-[0-9]{4}$',
        'LY': R'^[0-9]{5}$',
        'MA': R'^[0-9]{5}$',
        'MC': R'^980[0-9]{2}$',
        'MD': R'^MD-?[0-9]{4}$',
        'ME': R'^[0-9]{5}$',
        'MF': R'^[0-9]{5}$',
        'MG': R'^[0-9]{3}$',
        'MH': R'^[0-9]{5}$',
        'MK': R'^[0-9]{4}$',
        'MM': R'^[0-9]{5}$',
        'MN': R'^[0-9]{5}$',
        'MP': R'^[0-9]{5}$',
        'MQ': R'^[0-9]{5}$',
        'MT': R'^[A-Z]{3}[0-9]{4}$',
        'MV': R'^[0-9]{4,5}$',
        'MX': R'^[0-9]{5}$',
        'MY': R'^[0-9]{5}$',
        'MZ': R'^[0-9]{4}$',
        'NA': R'^[0-9]{5}$',
        'NC': R'^[0-9]{5}$',
        'NE': R'^[0-9]{4}$',
        'NF': R'^[0-9]{4}$',
        'NG': R'^[0-9]{6}$',
        'NI': R'^[0-9]{3}-[0-9]{3}-[0-9]$',
        'NL': R'^[0-9]{4}[A-Z]{2}$',
        'NO': R'^[0-9]{4}$',
        'NP': R'^[0-9]{5}$',
        'NZ': R'^[0-9]{4}$',
        'OM': R'^[0-9]{3}$',
        'PA': R'^[0-9]{6}$',
        'PE': R'^[0-9]{5}$',
        'PF': R'^[0-9]{5}$',
        'PG': R'^[0-9]{3}$',
        'PH': R'^[0-9]{4}$',
        'PK': R'^[0-9]{5}$',
        'PL': R'^[0-9]{2}-?[0-9]{3}$',
        'PM': R'^[0-9]{5}$',
        'PN': R'^[A-Z]{4}[0-9][A-Z]{2}$',
        'PR': R'^[0-9]{5}$',
        'PT': R'^[0-9]{4}(-?[0-9]{3})?$',
        'PW': R'^[0-9]{5}$',
        'PY': R'^[0-9]{4}$',
        'RE': R'^[0-9]{5}$',
        'RO': R'^[0-9]{6}$',
        'RS': R'^[0-9]{5}$',
        'RU': R'^[0-9]{6}$',
        'SA': R'^[0-9]{5}$',
        'SD': R'^[0-9]{5}$',
        'SE': R'^[0-9]{5}$',
        'SG': R'^([0-9]{2}|[0-9]{4}|[0-9]{6})$',
        'SH': R'^(STHL1ZZ|TDCU1ZZ)$',
        'SI': R'^(SI-)?[0-9]{4}$',
        'SK': R'^[0-9]{5}$',
        'SM': R'^[0-9]{5}$',
        'SN': R'^[0-9]{5}$',
        'SV': R'^01101$',
        'SZ': R'^[A-Z][0-9]{3}$',
        'TC': R'^TKCA1ZZ$',
        'TD': R'^[0-9]{5}$',
        'TH': R'^[0-9]{5}$',
        'TJ': R'^[0-9]{6}$',
        'TM': R'^[0-9]{6}$',
        'TN': R'^[0-9]{4}$',
        'TR': R'^[0-9]{5}$',
        'TT': R'^[0-9]{6}$',
        'TW': R'^[0-9]{5}$',
        'UA': R'^[0-9]{5}$',
        'US': R'^[0-9]{5}(-[0-9]{4}|-[0-9]{6})?$',
        'UY': R'^[0-9]{5}$',
        'UZ': R'^[0-9]{6}$',
        'VA': R'^00120$',
        'VC': R'^VC[0-9]{4}',
        'VE': R'^[0-9]{4}[A-Z]?$',
        'VG': R'^VG[0-9]{4}$',
        'VI': R'^[0-9]{5}$',
        'VN': R'^[0-9]{6}$',
        'WF': R'^[0-9]{5}$',
        'XK': R'^[0-9]{5}$',
        'YT': R'^[0-9]{5}$',
        'ZA': R'^[0-9]{4}$',
        'ZM': R'^[0-9]{5}$',
    }

    title = models.CharField(
        _("Title"), max_length=64, choices=TITLE_CHOICES,
        blank=True, null=True)
    first_name = models.CharField(
        _("First name"), max_length=255, blank=True, null=True)
    last_name = models.CharField(_("Last name"), max_length=255, blank=True)

    # We use quite a few lines of an address as they are often quite long and
    # it's easier to just hide the unnecessary ones than add extra ones.
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(
        _("Second line of address"), max_length=255, blank=True, null=True)
    line3 = models.CharField(
        _("Third line of address"), max_length=255, blank=True, null=True)
    line4 = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(
        _("State/County"), max_length=255, blank=True, null=True)
    postcode = models.CharField(
        _("Post/Zip-code"), max_length=64, blank=True, null=True)
    country = models.ForeignKey('address.Country', verbose_name=_("Country"))

    #: A field only used for searching addresses - this contains all the
    #: relevant fields.  This is effectively a poor man's Solr text field.
    search_text = models.CharField(
        _("Search text - used only for searching addresses"),
        max_length=1000)

    class Meta:
        abstract = True
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')

    # Saving

    def save(self, *args, **kwargs):
        self._clean_fields()
        self._update_search_text()
        super(AbstractAddress, self).save(*args, **kwargs)

    def _clean_fields(self):
        for field in ['first_name', 'last_name', 'line1', 'line2', 'line3',
                      'line4', 'state', 'postcode']:
            if self.__dict__[field]:
                self.__dict__[field] = self.__dict__[field].strip()

        self.clean_postcode()

    def clean_postcode(self):
        """
        Validate postcode given the country
        """
        if self.postcode:
            # Ensure postcodes are always uppercase
            self.postcode = self.postcode.upper()

            postcode = self.postcode.replace(' ', '')
            country_code = self.country.iso_3166_1_a2
            regex = self.POSTCODES_REGEX.get(country_code, None)

            # Validate postcode against regext for the country if available
            if regex and not re.match(regex, postcode):
                raise exceptions.ValidationError("Invalid postcode")

    def _update_search_text(self):
        search_fields = filter(
            bool, [self.first_name, self.last_name,
                   self.line1, self.line2, self.line3, self.line4,
                   self.state, self.postcode, self.country.name])
        self.search_text = ' '.join(search_fields)

    # Properties

    @property
    def city(self):
        # Common alias
        return self.line4

    @property
    def summary(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        return u", ".join(self.active_address_fields())

    @property
    def salutation(self):
        """
        Name (including title)
        """
        return self.join_fields(
            ('title', 'first_name', 'last_name'),
            separator=u" ")

    @property
    def name(self):
        return self.join_fields(
            ('first_name', 'last_name'),
            separator=u" ")

    # Helpers

    def join_fields(self, fields, separator=u", "):
        field_values = []
        for field in fields:
            if field == 'title':
                value = self.get_title_display()
            else:
                value = getattr(self, field)
            field_values.append(value)
        return separator.join(filter(bool, field_values))

    def populate_alternative_model(self, address_model):
        """
        For populating an address model using the matching fields
        from this one.

        This is used to convert a user address to a shipping address
        as part of the checkout process.
        """
        destination_field_names = [
            field.name for field in address_model._meta.fields]
        for field_name in [field.name for field in self._meta.fields]:
            if field_name in destination_field_names and field_name != 'id':
                setattr(address_model, field_name, getattr(self, field_name))

    def active_address_fields(self):
        """
        Return the non-empty components of the address, but merging the
        title, first_name and last_name into a single line.
        """
        self._clean_fields()
        fields = filter(
            bool, [self.salutation, self.line1, self.line2,
                   self.line3, self.line4, self.state, self.postcode])
        if self.country:
            fields.append(self.country.name)
        return fields

    def __unicode__(self):
        return self.summary


class AbstractCountry(models.Model):
    """
    International Organization for Standardization (ISO) 3166-1 Country list.
    """
    iso_3166_1_a2 = models.CharField(_('ISO 3166-1 alpha-2'), max_length=2,
                                     primary_key=True)
    iso_3166_1_a3 = models.CharField(_('ISO 3166-1 alpha-3'), max_length=3,
                                     null=True, db_index=True)
    iso_3166_1_numeric = models.PositiveSmallIntegerField(
        _('ISO 3166-1 numeric'), null=True, db_index=True)
    name = models.CharField(_('Official name (CAPS)'), max_length=128)
    printable_name = models.CharField(_('Country name'), max_length=128)

    display_order = models.PositiveSmallIntegerField(
        _("Display order"), default=0, db_index=True,
        help_text=_('Higher the number, higher the country in the list.'))

    is_shipping_country = models.BooleanField(_("Is Shipping Country"),
                                              default=False, db_index=True)

    class Meta:
        abstract = True
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ('-display_order', 'name',)

    def __unicode__(self):
        return self.printable_name


class AbstractShippingAddress(AbstractAddress):
    """
    A shipping address.

    A shipping address should not be edited once the order has been placed -
    it should be read-only after that.
    """
    phone_number = models.CharField(_("Phone number"), max_length=32,
                                    blank=True, null=True)
    notes = models.TextField(
        blank=True, null=True,
        verbose_name=_('Courier instructions'),
        help_text=_("For example, leave the parcel in the wheelie bin "
                    "if I'm not in."))

    class Meta:
        abstract = True
        verbose_name = _("Shipping address")
        verbose_name_plural = _("Shipping addresses")

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
    A user's address.  A user can have many of these and together they form an
    'address book' of sorts for the user.

    We use a separate model for shipping and billing (even though there will be
    some data duplication) because we don't want shipping/billing addresses
    changed or deleted once an order has been placed.  By having a separate
    model, we allow users the ability to add/edit/delete from their address
    book without affecting orders already placed.
    """
    user = models.ForeignKey(
        AUTH_USER_MODEL, related_name='addresses', verbose_name=_("User"))

    #: Whether this address is the default for shipping
    is_default_for_shipping = models.BooleanField(
        _("Default shipping address?"), default=False)

    #: Whether this address should be the default for billing.
    is_default_for_billing = models.BooleanField(
        _("Default billing address?"), default=False)

    #: We keep track of the number of times an address has been used
    #: as a shipping address so we can show the most popular ones
    #: first at the checkout.
    num_orders = models.PositiveIntegerField(_("Number of Orders"), default=0)

    #: A hash is kept to try and avoid duplicate addresses being added
    #: to the address book.
    hash = models.CharField(_("Address Hash"), max_length=255, db_index=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    def generate_hash(self):
        """
        Returns a hash of the address summary
        """
        # We use an upper-case version of the summary
        return zlib.crc32(self.summary.strip().upper().encode('UTF8'))

    def save(self, *args, **kwargs):
        """
        Save a hash of the address fields
        """
        # Save a hash of the address fields so we can check whether two
        # addresses are the same to avoid saving duplicates
        self.hash = self.generate_hash()
        # Ensure that each user only has one default shipping address
        # and billing address
        self._ensure_defaults_integrity()
        super(AbstractUserAddress, self).save(*args, **kwargs)

    def _ensure_defaults_integrity(self):
        if self.is_default_for_shipping:
            self.__class__._default_manager.filter(
                user=self.user,
                is_default_for_shipping=True).update(
                    is_default_for_shipping=False)
        if self.is_default_for_billing:
            self.__class__._default_manager.filter(
                user=self.user,
                is_default_for_billing=True).update(
                    is_default_for_billing=False)

    class Meta:
        abstract = True
        verbose_name = _("User address")
        verbose_name_plural = _("User addresses")
        ordering = ['-num_orders']


class AbstractBillingAddress(AbstractAddress):

    class Meta:
        abstract = True
        verbose_name_plural = _("Billing address")
        verbose_name_plural = _("Billing addresses")

    @property
    def order(self):
        """
        Return the order linked to this shipping address
        """
        orders = self.order_set.all()
        if not orders:
            return None
        return orders[0]
