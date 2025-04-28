from django import forms

class ZipUploadForm(forms.Form):
    zip_file = forms.FileField(
        label='Upload ZIP of DICOMs',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.zip'
        })
    )

from django import forms
from .models import Patient
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

class AddCaseForm(forms.ModelForm):
    zip_file = forms.FileField(label='Upload ZIP of DICOM folder')

    class Meta:
        model = Patient
        fields = [
            'patient_name','age','sex','modality',
            'study_type','receiving_date','institution_name',
        ]
        widgets = {
            'receiving_date': forms.DateInput(attrs={'type':'date'}),
        }

class AssignPhysicianForm(forms.Form):
    physician = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(role='doctor'),
        label='Assign Physician'
    )