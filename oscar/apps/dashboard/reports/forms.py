from django import forms

from oscar.core.loading import import_module
report_utils = import_module('dashboard.reports.utils', ['GeneratorRepository'])

class ReportForm(forms.Form):
    
    generators = report_utils.GeneratorRepository().get_report_generators()
    
    type_choices = []
    for generator in generators:
        type_choices.append((generator.code, generator.description))
    report_type = forms.ChoiceField(widget=forms.Select(), choices=type_choices)
    date_from = forms.DateField()
    date_to = forms.DateField()
    
    def clean(self):
        if 'date_from' in self.cleaned_data and 'date_to' in self.cleaned_data and self.cleaned_data['date_from'] > self.cleaned_data['date_to']:
            raise forms.ValidationError("Your start date must be before your end date")
        return self.cleaned_data
   