from django import forms
from django.db.models.loading import get_model

OrderNote = get_model('order', 'OrderNote')


class OrderSearchForm(forms.Form):
    order_number = forms.CharField(required=False, label="Order number")
    name = forms.CharField(required=False, label="Customer name")
    product_title = forms.CharField(required=False, label="Product name")
    product_id = forms.CharField(required=False, label="Product ID")

    status = forms.CharField(required=False, label="Shipping status")

    date_formats = ('%d/%m/%Y',)
    date_from = forms.DateField(required=False, label="Date from", input_formats=date_formats)
    date_to = forms.DateField(required=False, label="Date to", input_formats=date_formats)    

    voucher = forms.CharField(required=False, label="Voucher code")
    payment_method = forms.CharField(label="Payment method", required=False)

    format_choices = (('html', 'HTML'),
                      ('csv', 'CSV'),)
    response_format = forms.ChoiceField(widget=forms.RadioSelect, 
            choices=format_choices, initial='html', label="Get results as")


class OrderNoteForm(forms.ModelForm):

    class Meta:
        model = OrderNote
        exclude = ('order', 'user', 'note_type')
