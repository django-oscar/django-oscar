from django import forms
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class
from oscar.forms.widgets import DatePickerInput


GeneratorRepository = get_class('dashboard.reports.utils',
                                'GeneratorRepository')


class ReportForm(forms.Form):
    generators = GeneratorRepository().get_report_generators()

    type_choices = []
    for generator in generators:
        type_choices.append((generator.code, generator.description))
    report_type = forms.ChoiceField(widget=forms.Select(),
                                    choices=type_choices,
                                    label=_("Report Type"),
                                    help_text=_("Only the offer and order"
                                                " reports use the selected"
                                                " date range"))

    date_from = forms.DateField(label=_("Date from"), required=False,
                                widget=DatePickerInput)
    date_to = forms.DateField(label=_("Date to"),
                              help_text=_("The report is inclusive of this"
                                          " date"),
                              required=False,
                              widget=DatePickerInput)
    download = forms.BooleanField(label=_("Download"), required=False)

    def clean(self):
        if ('date_from' in self.cleaned_data and 'date_to' in self.cleaned_data
                and self.cleaned_data['date_from'] >
                self.cleaned_data['date_to']):
            raise forms.ValidationError(_("Your start date must be before your"
                                          " end date"))
        return self.cleaned_data
