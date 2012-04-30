from django import forms

from django.db.models.loading import get_model

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')


class MetaDataForm(forms.ModelForm):

    class Meta:
        model = ConditionalOffer
        fields = ('name', 'description', 'start_date', 'end_date',)


class ConditionForm(forms.ModelForm):

    class Meta:
        model = Condition


class BenefitForm(forms.ModelForm):

    class Meta:
        model = Benefit


class PreviewForm(forms.Form):
    pass


class OfferSearchForm(forms.Form):
    name = forms.CharField(required=False, label="Offer name")
    is_active = forms.BooleanField(required=False)


def o():
    product_title = forms.CharField(required=False, label="Product name")
    product_id = forms.CharField(required=False, label="Product ID")

    status_choices = (('', '---------'),) + tuple([(v, v) for v in Order.all_statuses()])
    status = forms.ChoiceField(choices=status_choices, label="Status", required=False)

    date_formats = ('%d/%m/%Y',)
    date_from = forms.DateField(required=False, label="Date from", input_formats=date_formats)
    date_to = forms.DateField(required=False, label="Date to", input_formats=date_formats)

    voucher = forms.CharField(required=False, label="Voucher code")

    method_choices = (('', '---------'),) + tuple([(src.code, src.name) for src in SourceType.objects.all()])
    payment_method = forms.ChoiceField(label="Payment method", required=False,
                                       choices=method_choices)

    format_choices = (('html', 'HTML'),
                      ('csv', 'CSV'),)
    response_format = forms.ChoiceField(widget=forms.RadioSelect,
            choices=format_choices, initial='html', label="Get results as")
