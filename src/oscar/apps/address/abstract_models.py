import re
import zlib

from django.conf import settings
from django.core import exceptions
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from phonenumber_field.modelfields import PhoneNumberField

from oscar.core.compat import AUTH_USER_MODEL
from oscar.models.fields import UppercaseCharField


class AbstractAddress(models.Model):
    """
    Superclass address object

    This is subclassed and extended to provide models for
    user, shipping and billing addresses.
    """

    MR, MISS, MRS, MS, DR = ("Mr", "Miss", "Mrs", "Ms", "Dr")
    TITLE_CHOICES = (
        (MR, _("Mr")),
        (MISS, _("Miss")),
        (MRS, _("Mrs")),
        (MS, _("Ms")),
        (DR, _("Dr")),
    )

    POSTCODE_REQUIRED = "postcode" in settings.OSCAR_REQUIRED_ADDRESS_FIELDS

    # Regex for each country. Not listed countries don't use postcodes
    # Based on http://en.wikipedia.org/wiki/List_of_postal_codes
    POSTCODES_REGEX = {
        "AC": r"^[A-Z]{4}[0-9][A-Z]$",
        "AD": r"^AD[0-9]{3}$",
        "AF": r"^[0-9]{4}$",
        "AI": r"^AI-2640$",
        "AL": r"^[0-9]{4}$",
        "AM": r"^[0-9]{4}$",
        "AR": r"^([0-9]{4}|[A-Z][0-9]{4}[A-Z]{3})$",
        "AS": r"^[0-9]{5}(-[0-9]{4}|-[0-9]{6})?$",
        "AT": r"^[0-9]{4}$",
        "AU": r"^[0-9]{4}$",
        "AX": r"^[0-9]{5}$",
        "AZ": r"^AZ[0-9]{4}$",
        "BA": r"^[0-9]{5}$",
        "BB": r"^BB[0-9]{5}$",
        "BD": r"^[0-9]{4}$",
        "BE": r"^[0-9]{4}$",
        "BG": r"^[0-9]{4}$",
        "BH": r"^[0-9]{3,4}$",
        "BL": r"^[0-9]{5}$",
        "BM": r"^[A-Z]{2}([0-9]{2}|[A-Z]{2})",
        "BN": r"^[A-Z]{2}[0-9]{4}$",
        "BO": r"^[0-9]{4}$",
        "BR": r"^[0-9]{5}(-[0-9]{3})?$",
        "BT": r"^[0-9]{3}$",
        "BY": r"^[0-9]{6}$",
        "CA": r"^[A-Z][0-9][A-Z][0-9][A-Z][0-9]$",
        "CC": r"^[0-9]{4}$",
        "CH": r"^[0-9]{4}$",
        "CL": r"^([0-9]{7}|[0-9]{3}-[0-9]{4})$",
        "CN": r"^[0-9]{6}$",
        "CO": r"^[0-9]{6}$",
        "CR": r"^[0-9]{4,5}$",
        "CU": r"^[0-9]{5}$",
        "CV": r"^[0-9]{4}$",
        "CX": r"^[0-9]{4}$",
        "CY": r"^[0-9]{4}$",
        "CZ": r"^[0-9]{5}$",
        "DE": r"^[0-9]{5}$",
        "DK": r"^[0-9]{4}$",
        "DO": r"^[0-9]{5}$",
        "DZ": r"^[0-9]{5}$",
        "EC": r"^EC[0-9]{6}$",
        "EE": r"^[0-9]{5}$",
        "EG": r"^[0-9]{5}$",
        "ES": r"^[0-9]{5}$",
        "ET": r"^[0-9]{4}$",
        "FI": r"^[0-9]{5}$",
        "FK": r"^[A-Z]{4}[0-9][A-Z]{2}$",
        "FM": r"^[0-9]{5}(-[0-9]{4})?$",
        "FO": r"^[0-9]{3}$",
        "FR": r"^[0-9]{5}$",
        "GA": r"^[0-9]{2}.*[0-9]{2}$",
        "GB": r"^[A-Z][A-Z0-9]{1,3}[0-9][A-Z]{2}$",
        "GE": r"^[0-9]{4}$",
        "GF": r"^[0-9]{5}$",
        "GG": r"^([A-Z]{2}[0-9]{2,3}[A-Z]{2})$",
        "GI": r"^GX111AA$",
        "GL": r"^[0-9]{4}$",
        "GP": r"^[0-9]{5}$",
        "GR": r"^[0-9]{5}$",
        "GS": r"^SIQQ1ZZ$",
        "GT": r"^[0-9]{5}$",
        "GU": r"^[0-9]{5}$",
        "GW": r"^[0-9]{4}$",
        "HM": r"^[0-9]{4}$",
        "HN": r"^[0-9]{5}$",
        "HR": r"^[0-9]{5}$",
        "HT": r"^[0-9]{4}$",
        "HU": r"^[0-9]{4}$",
        "ID": r"^[0-9]{5}$",
        "IL": r"^([0-9]{5}|[0-9]{7})$",
        "IM": r"^IM[0-9]{2,3}[A-Z]{2}$$",
        "IN": r"^[0-9]{6}$",
        "IO": r"^[A-Z]{4}[0-9][A-Z]{2}$",
        "IQ": r"^[0-9]{5}$",
        "IR": r"^[0-9]{5}-[0-9]{5}$",
        "IS": r"^[0-9]{3}$",
        "IT": r"^[0-9]{5}$",
        "JE": r"^JE[0-9]{2}[A-Z]{2}$",
        "JM": r"^JM[A-Z]{3}[0-9]{2}$",
        "JO": r"^[0-9]{5}$",
        "JP": r"^[0-9]{3}-?[0-9]{4}$",
        "KE": r"^[0-9]{5}$",
        "KG": r"^[0-9]{6}$",
        "KH": r"^[0-9]{5}$",
        "KR": r"^[0-9]{5}$",
        "KY": r"^KY[0-9]-[0-9]{4}$",
        "KZ": r"^[0-9]{6}$",
        "LA": r"^[0-9]{5}$",
        "LB": r"^[0-9]{8}$",
        "LI": r"^[0-9]{4}$",
        "LK": r"^[0-9]{5}$",
        "LR": r"^[0-9]{4}$",
        "LS": r"^[0-9]{3}$",
        "LT": r"^(LT-)?[0-9]{5}$",
        "LU": r"^[0-9]{4}$",
        "LV": r"^LV-[0-9]{4}$",
        "LY": r"^[0-9]{5}$",
        "MA": r"^[0-9]{5}$",
        "MC": r"^980[0-9]{2}$",
        "MD": r"^MD-?[0-9]{4}$",
        "ME": r"^[0-9]{5}$",
        "MF": r"^[0-9]{5}$",
        "MG": r"^[0-9]{3}$",
        "MH": r"^[0-9]{5}$",
        "MK": r"^[0-9]{4}$",
        "MM": r"^[0-9]{5}$",
        "MN": r"^[0-9]{5}$",
        "MP": r"^[0-9]{5}$",
        "MQ": r"^[0-9]{5}$",
        "MT": r"^[A-Z]{3}[0-9]{4}$",
        "MV": r"^[0-9]{4,5}$",
        "MX": r"^[0-9]{5}$",
        "MY": r"^[0-9]{5}$",
        "MZ": r"^[0-9]{4}$",
        "NA": r"^[0-9]{5}$",
        "NC": r"^[0-9]{5}$",
        "NE": r"^[0-9]{4}$",
        "NF": r"^[0-9]{4}$",
        "NG": r"^[0-9]{6}$",
        "NI": r"^[0-9]{5}$",
        "NL": r"^[0-9]{4}[A-Z]{2}$",
        "NO": r"^[0-9]{4}$",
        "NP": r"^[0-9]{5}$",
        "NZ": r"^[0-9]{4}$",
        "OM": r"^[0-9]{3}$",
        "PA": r"^[0-9]{6}$",
        "PE": r"^[0-9]{5}$",
        "PF": r"^[0-9]{5}$",
        "PG": r"^[0-9]{3}$",
        "PH": r"^[0-9]{4}$",
        "PK": r"^[0-9]{5}$",
        "PL": r"^[0-9]{2}-?[0-9]{3}$",
        "PM": r"^[0-9]{5}$",
        "PN": r"^[A-Z]{4}[0-9][A-Z]{2}$",
        "PR": r"^[0-9]{5}$",
        "PT": r"^[0-9]{4}(-?[0-9]{3})?$",
        "PW": r"^[0-9]{5}$",
        "PY": r"^[0-9]{4}$",
        "RE": r"^[0-9]{5}$",
        "RO": r"^[0-9]{6}$",
        "RS": r"^[0-9]{5}$",
        "RU": r"^[0-9]{6}$",
        "SA": r"^[0-9]{5}$",
        "SD": r"^[0-9]{5}$",
        "SE": r"^[0-9]{5}$",
        "SG": r"^([0-9]{2}|[0-9]{4}|[0-9]{6})$",
        "SH": r"^(STHL1ZZ|TDCU1ZZ)$",
        "SI": r"^(SI-)?[0-9]{4}$",
        "SK": r"^[0-9]{5}$",
        "SM": r"^[0-9]{5}$",
        "SN": r"^[0-9]{5}$",
        "SV": r"^01101$",
        "SZ": r"^[A-Z][0-9]{3}$",
        "TC": r"^TKCA1ZZ$",
        "TD": r"^[0-9]{5}$",
        "TH": r"^[0-9]{5}$",
        "TJ": r"^[0-9]{6}$",
        "TM": r"^[0-9]{6}$",
        "TN": r"^[0-9]{4}$",
        "TR": r"^[0-9]{5}$",
        "TT": r"^[0-9]{6}$",
        "TW": r"^([0-9]{3}|[0-9]{5})$",
        "UA": r"^[0-9]{5}$",
        "US": r"^[0-9]{5}(-[0-9]{4}|-[0-9]{6})?$",
        "UY": r"^[0-9]{5}$",
        "UZ": r"^[0-9]{6}$",
        "VA": r"^00120$",
        "VC": r"^VC[0-9]{4}",
        "VE": r"^[0-9]{4}[A-Z]?$",
        "VG": r"^VG[0-9]{4}$",
        "VI": r"^[0-9]{5}$",
        "VN": r"^[0-9]{6}$",
        "WF": r"^[0-9]{5}$",
        "XK": r"^[0-9]{5}$",
        "YT": r"^[0-9]{5}$",
        "ZA": r"^[0-9]{4}$",
        "ZM": r"^[0-9]{5}$",
    }

    title = models.CharField(
        pgettext_lazy("Treatment Pronouns for the customer", "Title"),
        max_length=64,
        choices=TITLE_CHOICES,
        blank=True,
    )
    first_name = models.CharField(_("First name"), max_length=255, blank=True)
    last_name = models.CharField(_("Last name"), max_length=255, blank=True)

    # We use quite a few lines of an address as they are often quite long and
    # it's easier to just hide the unnecessary ones than add extra ones.
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True)
    line3 = models.CharField(_("Third line of address"), max_length=255, blank=True)
    line4 = models.CharField(_("City"), max_length=255, blank=True)
    state = models.CharField(_("State/County"), max_length=255, blank=True)
    postcode = UppercaseCharField(_("Post/Zip-code"), max_length=64, blank=True)
    country = models.ForeignKey(
        "address.Country", on_delete=models.CASCADE, verbose_name=_("Country")
    )

    # A field only used for searching addresses - this contains all the
    # `search_fields`.  This is effectively a poor man's Solr text field.
    search_text = models.TextField(
        _("Search text - used only for searching addresses"), editable=False
    )
    search_fields = [
        "first_name",
        "last_name",
        "line1",
        "line2",
        "line3",
        "line4",
        "state",
        "postcode",
        "country",
    ]

    # Fields, used for `summary` property definition and hash generation.
    base_fields = hash_fields = [
        "salutation",
        "line1",
        "line2",
        "line3",
        "line4",
        "state",
        "postcode",
        "country",
    ]

    def __str__(self):
        return self.summary

    class Meta:
        abstract = True
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    # Saving

    def save(self, *args, **kwargs):
        self._update_search_text()
        super().save(*args, **kwargs)

    def clean(self):
        # Strip all whitespace
        for field in [
            "first_name",
            "last_name",
            "line1",
            "line2",
            "line3",
            "line4",
            "state",
            "postcode",
        ]:
            if self.__dict__[field]:
                self.__dict__[field] = self.__dict__[field].strip()

        # Ensure postcodes are valid for country
        self.ensure_postcode_is_valid_for_country()

    def ensure_postcode_is_valid_for_country(self):
        """
        Validate postcode given the country
        """
        if not self.postcode and self.POSTCODE_REQUIRED and self.country_id:
            country_code = self.country.iso_3166_1_a2
            regex = self.POSTCODES_REGEX.get(country_code, None)
            if regex:
                msg = _("Addresses in %(country)s require a valid postcode") % {
                    "country": self.country
                }
                raise exceptions.ValidationError(msg)

        if self.postcode and self.country_id:
            # Ensure postcodes are always uppercase
            postcode = self.postcode.upper().replace(" ", "")
            country_code = self.country.iso_3166_1_a2
            regex = self.POSTCODES_REGEX.get(country_code, None)

            # Validate postcode against regex for the country if available
            if regex and not re.match(regex, postcode):
                msg = _("The postcode '%(postcode)s' is not valid for %(country)s") % {
                    "postcode": self.postcode,
                    "country": self.country,
                }
                raise exceptions.ValidationError({"postcode": [msg]})

    def _update_search_text(self):
        self.search_text = self.join_fields(self.search_fields, separator=" ")

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
        return ", ".join(self.active_address_fields())

    @property
    def salutation(self):
        """
        Name (including title)
        """
        return self.join_fields(
            ("title", "first_name", "last_name"), separator=" "
        ).strip()

    @property
    def name(self):
        return self.join_fields(("first_name", "last_name"), separator=" ")

    # Helpers

    def get_field_values(self, fields):
        field_values = []
        for field in fields:
            # Title is special case
            if field == "title":
                value = self.get_title_display()
            elif field == "country":
                try:
                    value = self.country.printable_name
                except exceptions.ObjectDoesNotExist:
                    value = ""
            elif field == "salutation":
                value = self.salutation
            else:
                value = getattr(self, field)
            field_values.append(value)
        return field_values

    def get_address_field_values(self, fields):
        """
        Returns set of field values within the salutation and country.
        """
        field_values = [f.strip() for f in self.get_field_values(fields) if f]
        return field_values

    def generate_hash(self):
        """
        Returns a hash of the address, based on standard set of fields, listed
        out in `hash_fields` property.
        """
        field_values = self.get_address_field_values(self.hash_fields)
        # Python 2 and 3 generates CRC checksum in different ranges, so
        # in order to generate platform-independent value we apply
        # `& 0xffffffff` expression.
        return zlib.crc32(", ".join(field_values).upper().encode("UTF8")) & 0xFFFFFFFF

    def join_fields(self, fields, separator=", "):
        """
        Join a sequence of fields using the specified separator
        """
        field_values = self.get_field_values(fields)
        return separator.join(filter(bool, field_values))

    def populate_alternative_model(self, address_model):
        """
        For populating an address model using the matching fields
        from this one.

        This is used to convert a user address to a shipping address
        as part of the checkout process.
        """
        destination_field_names = [field.name for field in address_model._meta.fields]
        for field_name in [field.name for field in self._meta.fields]:
            if field_name in destination_field_names and field_name != "id":
                setattr(address_model, field_name, getattr(self, field_name))

    def active_address_fields(self):
        """
        Returns the non-empty components of the address, but merging the
        title, first_name and last_name into a single line. It uses fields
        listed out in `base_fields` property.
        """
        return self.get_address_field_values(self.base_fields)


class AbstractCountry(models.Model):
    """
    `ISO 3166 Country Codes <https://www.iso.org/iso-3166-country-codes.html>`_

    The field names are a bit awkward, but kept for backwards compatibility.
    pycountry's syntax of alpha2, alpha3, name and official_name seems sane.
    """

    iso_3166_1_a2 = models.CharField(
        _("ISO 3166-1 alpha-2"), max_length=2, primary_key=True
    )
    iso_3166_1_a3 = models.CharField(_("ISO 3166-1 alpha-3"), max_length=3, blank=True)
    iso_3166_1_numeric = models.CharField(
        _("ISO 3166-1 numeric"), blank=True, max_length=3
    )

    #: The commonly used name; e.g. 'United Kingdom'
    printable_name = models.CharField(_("Country name"), max_length=128, db_index=True)
    #: The full official name of a country
    #: e.g. 'United Kingdom of Great Britain and Northern Ireland'
    name = models.CharField(_("Official name"), max_length=128)

    display_order = models.PositiveSmallIntegerField(
        _("Display order"),
        default=0,
        db_index=True,
        help_text=_("Higher the number, higher the country in the list."),
    )

    is_shipping_country = models.BooleanField(
        _("Is shipping country"), default=False, db_index=True
    )

    class Meta:
        abstract = True
        app_label = "address"
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")
        ordering = (
            "-display_order",
            "printable_name",
        )

    def __str__(self):
        return self.printable_name or self.name

    @property
    def code(self):
        """
        Shorthand for the ISO 3166 Alpha-2 code
        """
        return self.iso_3166_1_a2

    @property
    def numeric_code(self):
        """
        Shorthand for the ISO 3166 numeric code.

        :py:attr:`.iso_3166_1_numeric` used to wrongly be a integer field, but has to
        be padded with leading zeroes. It's since been converted to a char
        field, but the database might still contain non-padded strings. That's
        why the padding is kept.
        """
        return "%.03d" % int(self.iso_3166_1_numeric)


class AbstractShippingAddress(AbstractAddress):
    """
    A shipping address.

    A shipping address should not be edited once the order has been placed -
    it should be read-only after that.

    NOTE:
    ShippingAddress is a model of the order app. But moving it there is tricky
    due to circular import issues that are amplified by get_model/get_class
    calls pre-Django 1.7 to register receivers. So...
    TODO: Once Django 1.6 support is dropped, move AbstractBillingAddress and
    AbstractShippingAddress to the order app, and move
    PartnerAddress to the partner app.
    """

    phone_number = PhoneNumberField(
        _("Phone number"),
        blank=True,
        help_text=_("In case we need to call you about your order"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Instructions"),
        help_text=_("Tell us anything we should know when delivering your order."),
    )

    class Meta:
        abstract = True
        # ShippingAddress is registered in order/models.py
        app_label = "order"
        verbose_name = _("Shipping address")
        verbose_name_plural = _("Shipping addresses")

    @property
    def order(self):
        """
        Return the order linked to this shipping address
        """
        return self.order_set.first()


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
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("User"),
    )

    #: Whether this address is the default for shipping
    is_default_for_shipping = models.BooleanField(
        _("Default shipping address?"), default=False
    )

    #: Whether this address should be the default for billing.
    is_default_for_billing = models.BooleanField(
        _("Default billing address?"), default=False
    )

    #: We keep track of the number of times an address has been used
    #: as a shipping address so we can show the most popular ones
    #: first at the checkout.
    num_orders_as_shipping_address = models.PositiveIntegerField(
        _("Number of Orders as Shipping Address"), default=0
    )

    #: Same as previous, but for billing address.
    num_orders_as_billing_address = models.PositiveIntegerField(
        _("Number of Orders as Billing Address"), default=0
    )

    #: A hash is kept to try and avoid duplicate addresses being added
    #: to the address book.
    hash = models.CharField(
        _("Address Hash"), max_length=255, db_index=True, editable=False
    )
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

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
        super().save(*args, **kwargs)

    def _ensure_defaults_integrity(self):
        if self.is_default_for_shipping:
            self.__class__._default_manager.filter(
                user=self.user, is_default_for_shipping=True
            ).update(is_default_for_shipping=False)
        if self.is_default_for_billing:
            self.__class__._default_manager.filter(
                user=self.user, is_default_for_billing=True
            ).update(is_default_for_billing=False)

    class Meta:
        abstract = True
        app_label = "address"
        verbose_name = _("User address")
        verbose_name_plural = _("User addresses")
        ordering = ["-num_orders_as_shipping_address"]
        unique_together = ("user", "hash")

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        qs = self.__class__.objects.filter(user=self.user, hash=self.generate_hash())
        if self.id:
            qs = qs.exclude(id=self.id)
        if qs.exists():
            raise exceptions.ValidationError(
                {"__all__": [_("This address is already in your address book")]}
            )


class AbstractBillingAddress(AbstractAddress):
    class Meta:
        abstract = True
        # BillingAddress is registered in order/models.py
        app_label = "order"
        verbose_name = _("Billing address")
        verbose_name_plural = _("Billing addresses")

    @property
    def order(self):
        """
        Return the order linked to this shipping address
        """
        return self.order_set.first()


class AbstractPartnerAddress(AbstractAddress):
    """
    A partner can have one or more addresses. This can be useful e.g. when
    determining US tax which depends on the origin of the shipment.
    """

    partner = models.ForeignKey(
        "partner.Partner",
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("Partner"),
    )

    class Meta:
        abstract = True
        app_label = "partner"
        verbose_name = _("Partner address")
        verbose_name_plural = _("Partner addresses")
