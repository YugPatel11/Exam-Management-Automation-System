"""
Forms for Faculty Assignment Management.
"""
from django import forms
from django.core.validators import FileExtensionValidator


class AssignmentUploadForm(forms.Form):
    """
    Form to handle CSV file uploads for Faculty and Coordinator assignments.
    """
    csv_file = forms.FileField(
        label='Select CSV File',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-slate-500 dark:text-slate-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 dark:file:bg-slate-800 dark:file:text-slate-300 dark:hover:file:bg-slate-700 transition cursor-pointer',
            'accept': '.csv'
        })
    )
