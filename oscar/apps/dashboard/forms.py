from django import forms


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
