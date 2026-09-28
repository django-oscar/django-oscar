import json

from django import forms
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class
from oscar.forms.widgets import DatePickerInput

GeneratorRepository = get_class("dashboard.reports.utils", "GeneratorRepository")


class ReportForm(forms.Form):
    generators = GeneratorRepository().get_report_generators()

    type_choices = []
    for generator in generators:
        type_choices.append((generator.code, generator.description))
    report_type = forms.ChoiceField(
        widget=forms.Select(),
        choices=type_choices,
        label=_("Report Type"),
    )

    date_from = forms.DateField(
        label=_("Date from"), required=False, widget=DatePickerInput
    )
    date_to = forms.DateField(
        label=_("Date to"),
        help_text=_("The report is inclusive of this date"),
        required=False,
        widget=DatePickerInput,
    )
    download = forms.BooleanField(label=_("Download"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Used by the dashboard JS to hide the fields a report doesn't use
        self.fields["report_type"].widget.attrs["data-unsupported-fields"] = json.dumps(
            self.get_unsupported_field_ids()
        )

    def get_generator(self, code):
        for generator in self.generators:
            if generator.code == code:
                return generator
        return None

    def get_unsupported_fields(self, generator):
        return [
            name
            for name in generator.get_unsupported_form_fields()
            if name in self.fields
        ]

    def get_unsupported_field_ids(self):
        field_ids = {}
        for generator in self.generators:
            ids = [
                self[name].auto_id
                for name in self.get_unsupported_fields(generator)
                if self[name].auto_id
            ]
            if ids:
                field_ids[generator.code] = ids
        return field_ids

    def clean_unsupported_fields(self, generator):
        for name in self.get_unsupported_fields(generator):
            if self.cleaned_data.get(name):
                self.add_error(
                    None,
                    _("%(field)s can't be used with the %(report)s report")
                    % {
                        "field": self.fields[name].label,
                        "report": generator.description,
                    },
                )

    def clean(self):
        cleaned_data = super().clean()
        generator = self.get_generator(cleaned_data.get("report_type"))
        if generator is not None:
            self.clean_unsupported_fields(generator)

        date_from = cleaned_data.get("date_from", None)
        date_to = cleaned_data.get("date_to", None)
        if all([date_from, date_to]) and date_from > date_to:
            raise forms.ValidationError(
                _("Your start date must be before your end date")
            )
        return cleaned_data
