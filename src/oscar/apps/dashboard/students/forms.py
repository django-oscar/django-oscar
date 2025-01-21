import datetime

from django import forms
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.core.loading import get_class, get_model
from oscar.forms.mixins import PhoneNumberMixin
from oscar.forms.widgets import DatePickerInput
from server.apps.school.models import GRADES, GENDER

Student = get_model("school", "Student")

class StudentForm(forms.ModelForm):
    STATUS_CHOICES = (
        (True, 'Active'),
        (False, 'Inactive')
    )
    
    is_active = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Student
        fields = ['full_name_en', 'full_name_ar', 'date_of_birth', 'gender', 'grade', 'is_active']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'full_name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name_ar': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def clean_is_active(self):
        """Convert the string 'True'/'False' to boolean value"""
        return self.cleaned_data['is_active'] == 'True'
class StudentSearchForm(forms.Form):
    national_id = forms.CharField(required=False, label=_("National ID"))
    full_name = forms.CharField(required=False, label=_("Full name"))
    grade = forms.ChoiceField(required=False, label=_("Grade"), choices=GRADES)
    gender = forms.ChoiceField(required=False, label=_("Gender"), choices=GENDER)
    parent = forms.CharField(required=False, label=_("Parent"))

    birth_date_from = forms.DateField(
        required=False, label=_("Date from"), widget=DatePickerInput
    )
    birth_date_to = forms.DateField(
        required=False, label=_("Date to"), widget=DatePickerInput
    )



