from django import forms

from oscar.core.loading import get_model


class WeightBasedForm(forms.ModelForm):

    class Meta:
        model = get_model('shipping', 'WeightBased')
        fields = ['name', 'description', 'default_weight', 'countries']


class WeightBandForm(forms.ModelForm):

    def __init__(self, method, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.method = method

    class Meta:
        model = get_model('shipping', 'WeightBand')
        fields = ('upper_limit', 'charge')
