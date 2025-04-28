from django import forms
from .models import Patient
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

class AddCaseForm(forms.ModelForm):
    # patient_id will be auto-generated or manually set in view; not part of form fields
    class Meta:
        model = Patient
        fields = [
            'patient_name', 'age', 'sex', 'modality',
            'study_type', 'institution_name',
        ]
        widgets = {
            'receiving_date': forms.DateInput(attrs={'type': 'date'}),
        }

class AssignPhysicianForm(forms.Form):
    physician = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(role='doctor'),
        label='Assign Physician'
    )
