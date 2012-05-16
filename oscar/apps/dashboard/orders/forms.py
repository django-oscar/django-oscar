from django import forms
from django.db.models.loading import get_model

Order = get_model('order', 'Order')
OrderNote = get_model('order', 'OrderNote')
ShippingAddress = get_model('order', 'ShippingAddress')
SourceType = get_model('payment', 'SourceType')


class OrderStatsForm(forms.Form):
    date_from = forms.DateField(required=False, label="From")
    date_to = forms.DateField(required=False, label="To")

    _filters = _description = None

    def _determine_filter_metadata(self):
        self._filters = {}
        self._description = 'All orders'
        if self.errors:
            return

        date_from = self.cleaned_data['date_from']
        date_to = self.cleaned_data['date_to']
        if date_from and date_to:
            self._filters = {'date_placed__range': [date_from, date_to]}
            self._description = 'Orders placed between %s and %s' % (date_from, date_to)
        elif date_from and not date_to:
            self._filters = {'date_placed__gt': date_from}
            self._description = 'Orders placed since %s' % (date_from,)
        elif not date_from and date_to:
            self._filters = {'date_placed__lt': date_to}
            self._description = 'Orders placed before %s' % (date_to,)
        else:
            self._filters = {}
            self._description = 'All orders'

    def get_filters(self):
        if self._filters is None:
            self._determine_filter_metadata()
        return self._filters

    def get_filter_description(self):
        if self._description is None:
            self._determine_filter_metadata()
        return self._description


class OrderSearchForm(forms.Form):
    order_number = forms.CharField(required=False, label="Order number")
    name = forms.CharField(required=False, label="Customer name")
    product_title = forms.CharField(required=False, label="Product name")
    upc = forms.CharField(required=False, label="UPC")
    partner_sku = forms.CharField(required=False, label="Partner SKU")

    status_choices = (('', '---------'),) + tuple([(v, v) for v in Order.all_statuses()])
    status = forms.ChoiceField(choices=status_choices, label="Status", required=False)

    date_from = forms.DateField(required=False, label="Date from")
    date_to = forms.DateField(required=False, label="Date to")

    voucher = forms.CharField(required=False, label="Voucher code")

    method_choices = (('', '---------'),) + tuple([(src.code, src.name) for src in SourceType.objects.all()])
    payment_method = forms.ChoiceField(label="Payment method", required=False,
                                       choices=method_choices)

    format_choices = (('html', 'HTML'),
                      ('csv', 'CSV'),)
    response_format = forms.ChoiceField(widget=forms.RadioSelect,
            choices=format_choices, initial='html', label="Get results as")


class OrderNoteForm(forms.ModelForm):

    class Meta:
        model = OrderNote
        exclude = ('order', 'user', 'note_type')


class ShippingAddressForm(forms.ModelForm):

    class Meta:
        model = ShippingAddress
        exclude = ('search_text',)
