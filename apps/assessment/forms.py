"""
Forms for Assessment Scheme Configuration.
"""
from django import forms
from apps.assessment.models import AssessmentComponent


class AssessmentComponentForm(forms.ModelForm):
    class Meta:
        model = AssessmentComponent
        fields = ['name', 'variable_name', 'max_marks']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white',
                'placeholder': 'e.g., Internal 1'
            }),
            'variable_name': forms.TextInput(attrs={
                'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white',
                'placeholder': 'e.g., I1'
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white',
                'placeholder': 'e.g., 30'
            }),
        }

