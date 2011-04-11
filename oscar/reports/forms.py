from datetime import date, datetime

from django import forms

class ReportForm(forms.Form):
    
    # @todo Make this dynamic
    type_choices = (
        ('orders', 'Orders'),
    )
    report_type = forms.ChoiceField(widget=forms.Select(), choices=type_choices)
    start_date = forms.DateField(widget=forms.widgets.DateInput(format="%d/%m/%Y"))
    end_date = forms.DateField(widget=forms.widgets.DateInput(format="%d/%m/%Y"))
    
    def clean(self):
        if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
            raise forms.ValidationError("Your start date must be before your end date")
        return self.cleaned_data
   