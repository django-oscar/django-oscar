from datetime import date, datetime
from calendar import monthrange
import re

from django import forms

from oscar.services import import_module

payment_models = import_module('payment.models', ['Bankcard'])

VISA, MASTERCARD, AMEX, MAESTRO, DISCOVER = ('Visa', 'Mastercard', 'American Express', 'Maestro', 'Discover')

def bankcard_type(number):
    number = str(number)
    if len(number) == 13:
        if number[0] == "4":
            return VISA
    elif len(number) == 14:
        if number[:2] == "36":
            return MASTERCARD
    elif len(number) == 15:
        if number[:2] in ("34", "37"):
            return AMEX
    elif len(number) == 16:
        if number[:4] == "6011":
            return DISCOVER
        if number[:2] in ("51", "52", "53", "54", "55"):
            return MASTERCARD
        if number[0] == "4":
            return VISA
    return None


class BankcardField(forms.CharField):

    def clean(self, value):
        """Check if given CC number is valid and one of the
           card types we accept"""
        non_decimal = re.compile(r'\D+')
        value = non_decimal.sub('', value.strip())    
           
        if value and (len(value) < 13 or len(value) > 16):
            raise forms.ValidationError("Please enter in a valid credit card number.")
        return super(BankcardField, self).clean(value)


class BankcardMonthWidget(forms.MultiWidget):
    """ 
    Widget containing two select boxes for selecting the month and year
    """
    def decompress(self, value):
        return [value.month, value.year] if value else [None, None]

    def format_output(self, rendered_widgets):
        html = u' '.join(rendered_widgets)
        return u'<span style="white-space: nowrap">%s</span>' % html


class BankcardMonthField(forms.MultiValueField):
    """
    A modified version of the snippet: http://djangosnippets.org/snippets/907/
    """
    MONTHS = [("%.2d" % x, "%.2d" % x) for x in xrange(1, 13)]
    YEARS = [(x, x) for x in xrange(date.today().year, date.today().year + 10)]
    
    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            forms.ChoiceField(choices=self.MONTHS,
                error_messages={'invalid': errors['invalid_month']}),
            forms.ChoiceField(choices=self.YEARS,
                error_messages={'invalid': errors['invalid_year']}),
        )
        super(BankcardMonthField, self).__init__(fields, *args, **kwargs)
        self.widget = BankcardMonthWidget(widgets = [fields[0].widget, fields[1].widget])

    def clean(self, value):
        expiry_date = super(BankcardMonthField, self).clean(value)
        if date.today() > expiry_date:
            raise forms.ValidationError("The expiration date you entered is in the past.")
        return expiry_date

    def compress(self, data_list):
        if data_list:
            if data_list[1] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_year']
                raise forms.ValidationError(error)
            if data_list[0] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_month']
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None 
    

class BankcardForm(forms.ModelForm):
    
    number = BankcardField(max_length=20, widget=forms.TextInput(attrs={'autocomplete':'off'}), label="Card number")
    name = forms.CharField(max_length=128, label="Name on card")
    ccv_number = forms.IntegerField(required = True, label = "CCV Number",
        max_value = 9999, widget=forms.TextInput(attrs={'size': '4'}))
    expiry_month = BankcardMonthField(required = True, label = "Valid to")
    
    class Meta:
        model = payment_models.Bankcard
        exclude = ('user', 'partner_reference')
        fields = ('number', 'name', 'expiry_month', 'ccv_number')
    
    
   