from datetime import date, datetime

from django import forms

from oscar.core.loading import import_module
report_utils = import_module('reports.utils', ['GeneratorRepository'])

class ReportForm(forms.Form):
    
    generators = report_utils.GeneratorRepository().get_report_generators()
    
    type_choices = []
    for generator in generators:
        type_choices.append((generator.code, generator.description))
    report_type = forms.ChoiceField(widget=forms.Select(), choices=type_choices)
    start_date = forms.DateField(widget=forms.widgets.DateInput(format="%d/%m/%Y"), 
                                 help_text='Format dd/mm/YYYY',
                                 input_formats=['%d/%m/%y', '%d/%m/%Y'])
    end_date = forms.DateField(widget=forms.widgets.DateInput(format="%d/%m/%Y"), 
                               help_text='Format dd/mm/YYYY',
                               input_formats=['%d/%m/%y', '%d/%m/%Y'])
    
    def clean(self):
        if 'start_date' in self.cleaned_data and 'end_date' in self.cleaned_data and self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
            raise forms.ValidationError("Your start date must be before your end date")
        return self.cleaned_data
   