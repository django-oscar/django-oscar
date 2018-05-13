import phonenumbers
from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.phonenumber import PhoneNumber


class PhoneNumberMixin(object):
    """Validation mixin for forms with a phone numbers, and optionally a country.

    It tries to validate the phone numbers, and on failure tries to validate
    them using a hint (the country provided), and treating it as a local number.

    Specify which fields to treat as phone numbers by specifying them in
    `phone_number_fields`, a dictionary of fields names and default kwargs
    for instantiation of the field.
    """
    country = None
    region_code = None
    # Since this mixin will be used with `ModelForms`, names of phone number
    # fields should match names of the related Model field
    phone_number_fields = {
        'phone_number': {
            'required': False,
            'help_text': '',
            'max_length': 32,
            'label': _('Phone number')
        },
    }

    def __init__(self, *args, **kwargs):
        super(PhoneNumberMixin, self).__init__(*args, **kwargs)

        # We can't use the PhoneNumberField here since we want validate the
        # phonenumber based on the selected country as a fallback when a local
        # number is entered. We add the fields in the init since on Python 2
        # using forms.Form as base class results in errors when using this
        # class as mixin.

        # If the model field already exists, copy existing properties from it
        for field_name, field_kwargs in self.phone_number_fields.items():
            for key in field_kwargs:
                try:
                    field_kwargs[key] = getattr(self.fields[field_name], key)
                except (KeyError, AttributeError):
                    pass

            self.fields[field_name] = forms.CharField(**field_kwargs)

    def get_country(self):
        # If the form data contains valid country information, we use that.
        if hasattr(self, 'cleaned_data') and 'country' in self.cleaned_data:
            return self.cleaned_data['country']
        # Oscar hides the field if there's only one country. Then (and only
        # then!) we can consider a country on the model instance.
        elif 'country' not in self.fields and hasattr(self.instance, 'country'):
            return self.instance.country

    def set_country_and_region_code(self):
        # Try hinting with the shipping country if we can determine one.
        self.country = self.get_country()
        if self.country:
            self.region_code = self.country.iso_3166_1_a2

    def clean_phone_number_field(self, field_name):
        number = self.cleaned_data.get(field_name)

        # Empty
        if number in validators.EMPTY_VALUES:
            return ''

        # Check for an international phone format
        try:
            phone_number = PhoneNumber.from_string(number)
        except phonenumbers.NumberParseException:

            if not self.region_code:
                # There is no shipping country, not a valid international number
                self.add_error(
                    field_name,
                    _(u'This is not a valid international phone format.'))
                return number

            # The PhoneNumber class does not allow specifying
            # the region. So we drop down to the underlying phonenumbers
            # library, which luckily allows parsing into a PhoneNumber
            # instance.
            try:
                phone_number = PhoneNumber.from_string(number,
                                                       region=self.region_code)
                if not phone_number.is_valid():
                    self.add_error(
                        field_name,
                        _(u'This is not a valid local phone format for %s.')
                        % self.country)
            except phonenumbers.NumberParseException:
                # Not a valid local or international phone number
                self.add_error(
                    field_name,
                    _(u'This is not a valid local or international phone format.'))
                return number

        return phone_number

    def clean(self):
        self.set_country_and_region_code()
        cleaned_data = super(PhoneNumberMixin, self).clean()
        for field_name in self.phone_number_fields:
            cleaned_data[field_name] = self.clean_phone_number_field(field_name)
        return cleaned_data
