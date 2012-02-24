from django import forms
from django.db.models.loading import get_model
from oscar.apps.dashboard.orders.models import OrderSummary

Order = get_model('order', 'Order')
OrderNote = get_model('order', 'OrderNote')
ShippingAddress = get_model('order', 'ShippingAddress')


class OrderSearchForm(forms.Form):
    order_number = forms.CharField(required=False, label="Order number")
    name = forms.CharField(required=False, label="Customer name")
    product_title = forms.CharField(required=False, label="Product name")
    product_id = forms.CharField(required=False, label="Product ID")

    status_choices = (('', '---------'),) + tuple([(v, v) for v in Order.all_statuses()])
    status = forms.ChoiceField(choices=status_choices, label="Status", required=False)

    date_formats = ('%d/%m/%Y',)
    date_from = forms.DateField(required=False, label="Date from", input_formats=date_formats)
    date_to = forms.DateField(required=False, label="Date to", input_formats=date_formats)

    voucher = forms.CharField(required=False, label="Voucher code")
    payment_method = forms.CharField(label="Payment method", required=False)

    format_choices = (('html', 'HTML'),
                      ('csv', 'CSV'),)
    response_format = forms.ChoiceField(widget=forms.RadioSelect,
            choices=format_choices, initial='html', label="Get results as")


class OrderSummaryForm(forms.Form):
    date_from = forms.DateField(required=False, label="From")
    date_to = forms.DateField(required=False, label="To")

    def get_filters(self):
        date_from = self.cleaned_data['date_from']
        date_to = self.cleaned_data['date_to']
        if date_from and date_to:
            return {'date_placed__range': [date_from, date_to]}
        elif date_from and not date_to:
            return {'date_placed__gt': date_from}
        elif not date_from and date_to:
            return {'date_placed__lt': date_to}
        return {}


class OrderNoteForm(forms.ModelForm):

    class Meta:
        model = OrderNote
        exclude = ('order', 'user', 'note_type')


class ShippingAddressForm(forms.ModelForm):

    class Meta:
        model = ShippingAddress
        exclude = ('search_text',)
