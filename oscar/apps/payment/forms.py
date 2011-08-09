from datetime import date, datetime
from calendar import monthrange
import re

from django import forms

from oscar.core.loading import import_module

address_models = import_module('address.models', ['Country'])
order_models = import_module('order.models', ['BillingAddress'])
payment_models = import_module('payment.models', ['Bankcard'])
import_module('payment.utils', ['Bankcard'], locals())

VISA, MASTERCARD, AMEX, MAESTRO, DISCOVER = ('Visa', 'Mastercard', 'American Express', 'Maestro', 'Discover')

def bankcard_type(number):
    u"""
    Returns the type of a bankcard based on its number.
    """
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

def luhn(card_number):
    u"""
    Tests whether a bankcard number passes the Luhn algorithm.
    """
    card_number = str(card_number)
    sum = 0
    num_digits = len(card_number)
    odd_even = num_digits & 1

    for i in range(0, num_digits):
        digit = int(card_number[i])
        if not (( i & 1 ) ^ odd_even ):
            digit = digit * 2
        if digit > 9:
            digit = digit - 9
        sum = sum + digit

    return (sum % 10) == 0


class BankcardNumberField(forms.CharField):

    def clean(self, value):
        """Check if given CC number is valid and one of the
           card types we accept"""
        non_decimal = re.compile(r'\D+')
        value = non_decimal.sub('', value.strip())    
           
        if value and not luhn(value):
            raise forms.ValidationError("Please enter a valid credit card number.")
        return super(BankcardNumberField, self).clean(value)


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
    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }
    num_years = 5

    def __init__(self, *args, **kwargs):
        
        # Allow the number of years to be specified
        if 'num_years' in kwargs:
            self.num_years = kwargs['num_years']
            del kwargs['num_years']
        
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            forms.ChoiceField(choices=self.month_choices(),
                error_messages={'invalid': errors['invalid_month']}),
            forms.ChoiceField(choices=self.year_choices(),
                error_messages={'invalid': errors['invalid_year']}),
        )
        
        super(BankcardMonthField, self).__init__(fields, *args, **kwargs)
        self.widget = BankcardMonthWidget(widgets = [fields[0].widget, fields[1].widget])
        
    def month_choices(self):
        return []
    
    def year_choices(self):
        return []


class BankcardExpiryMonthField(BankcardMonthField):
    """
    Expiry month
    """
    def month_choices(self):
        return [("%.2d" % x, "%.2d" % x) for x in xrange(1, 13)]

    def year_choices(self):
        return [(x, x) for x in xrange(date.today().year, date.today().year+self.num_years)]

    def clean(self, value):
        expiry_date = super(BankcardExpiryMonthField, self).clean(value)
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
    

class BankcardStartingMonthField(BankcardMonthField):
    """
    Starting month
    """
    def month_choices(self):
        months = [("%.2d" % x, "%.2d" % x) for x in xrange(1, 13)]
        months.insert(0, ("", "--"))
        return months

    def year_choices(self):
        years = [(x, x) for x in xrange( date.today().year - self.num_years, date.today().year)]
        years.insert(0, ("", "--"))
        return years

    def clean(self, value):
        starting_date = super(BankcardMonthField, self).clean(value)
        if starting_date and date.today() < starting_date:
            raise forms.ValidationError("The starting date you entered is in the future.")
        return starting_date

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
            return date(year, month, 1)
        return None 
    

class BankcardForm(forms.ModelForm):
    
    number = BankcardNumberField(max_length=20, widget=forms.TextInput(attrs={'autocomplete':'off'}), label="Card number")
    name = forms.CharField(max_length=128, label="Name on card")
    ccv_number = forms.IntegerField(required=True, label="CCV Number",
        max_value = 99999, widget=forms.TextInput(attrs={'size': '5'}))
    start_month = BankcardStartingMonthField(label="Valid from", required=False)
    expiry_month = BankcardExpiryMonthField(required=True, label = "Valid to")
    
    class Meta:
        model = payment_models.Bankcard
        exclude = ('user', 'partner_reference')
        fields = ('number', 'name', 'start_month', 'expiry_month', 'ccv_number')
        
    def get_bankcard_obj(self):
        """
        Returns a Bankcard object for use in payment processing.
        """
        kwargs = {
            'card_number': self.cleaned_data['number'],
            'expiry_date': self.cleaned_data['expiry_month'].strftime("%m/%y"),
            'ccv': self.cleaned_data['ccv_number'],
        }
        if self.cleaned_data['start_month']:
            kwargs['start_date'] = self.cleaned_data['start_month'].strftime("%m/%y")
        return Bankcard(**kwargs)
    

class BillingAddressForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(BillingAddressForm,self ).__init__(*args, **kwargs)
        self.set_country_queryset() 
        
    def set_country_queryset(self):    
        self.fields['country'].queryset = address_models.Country._default_manager.all()
    
    class Meta:
        model = order_models.BillingAddress
   