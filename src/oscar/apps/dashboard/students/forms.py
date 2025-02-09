import datetime
import os

from django import forms
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.core.loading import get_class, get_model
from oscar.forms.mixins import PhoneNumberMixin
from oscar.forms.widgets import DatePickerInput
from server.apps.school.models import GRADES, GENDER

Student = get_model("school", "Student")
PhotoValidationMixin = get_class("dashboard.students.validators", "PhotoValidationMixin")

class StudentForm(PhotoValidationMixin, forms.ModelForm):
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
        fields = ['full_name_en', 'full_name_ar', 'date_of_birth', 'gender', 'grade', 'parent_phone_number', 'is_active', 'photo']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'full_name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name_ar': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'parent_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

    def clean_is_active(self):
        """Convert the string 'True'/'False' to boolean value"""
        return self.cleaned_data['is_active'] == 'True'

class AddStudentForm(PhotoValidationMixin, forms.ModelForm):
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
        fields = ['national_id', 'full_name_en', 'full_name_ar', 'date_of_birth', 'gender', 'grade', 'parent_phone_number', 'is_active', 'photo']
        widgets = {
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'full_name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name_ar': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'parent_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

    def clean_is_active(self):
        """Convert the string 'True'/'False' to boolean value"""
        return self.cleaned_data['is_active'] == 'True'

class StudentSearchForm(forms.Form):
    national_id = forms.CharField(required=False, label=_("National ID"))
    full_name = forms.CharField(required=False, label=_("Full name"))
    grade = forms.ChoiceField(required=False, label=_("Grade"), choices=GRADES, initial=None)
    gender = forms.ChoiceField(required=False, label=_("Gender"), choices=GENDER, initial=None)
    birth_date_from = forms.DateField(
        required=False, label=_("Date from"), widget=DatePickerInput
    )
    birth_date_to = forms.DateField(
        required=False, label=_("Date to"), widget=DatePickerInput
    )
    parent_phone_number = forms.CharField(required=False, label=_("Parent Phone Number"))

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class StudentImagesImportForm(forms.Form):
    images = MultipleFileField(
        help_text='Select multiple images to upload. Supported formats: .jpg, .jpeg, .png'
    )

    def clean_images(self):
        images = self.files.getlist('images')
        valid_extensions = ['.jpg', '.jpeg', '.png']
        max_size = 2 * 1024 * 1024  # 2MB

        for image in images:
            # Check extension
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    f'Invalid file type for {image.name}. Allowed types: {", ".join(valid_extensions)}'
                )

            # Check size
            if image.size > max_size:
                raise forms.ValidationError(
                    f'File {image.name} is too large. Maximum size is 2MB.'
                )

        return images