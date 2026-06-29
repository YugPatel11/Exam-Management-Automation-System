"""
Forms for Academic Year Management.
"""
from django import forms
from django.core.validators import FileExtensionValidator
from apps.academic.models import AcademicYear


class AcademicYearForm(forms.ModelForm):
    """Form to create and edit Academic Year records."""

    class Meta:
        model = AcademicYear
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., 2023-24',
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional description or notes...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (
                    "mt-1 block w-full rounded-md border-slate-300 bg-white shadow-sm "
                    "focus:border-brand-500 focus:ring-brand-500 sm:text-sm "
                    "dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                )
            else:
                field.widget.attrs['class'] = (
                    "mt-1 block w-full rounded-md border-slate-300 shadow-sm "
                    "focus:border-brand-500 focus:ring-brand-500 sm:text-sm "
                    "dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                )


class AcademicStructureUploadForm(forms.Form):
    """Form to handle CSV/Excel file uploads for academic structure import."""

    structure_file = forms.FileField(
        label='Select CSV or Excel File',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])],
        widget=forms.FileInput(attrs={
            'class': (
                'block w-full text-sm text-slate-500 dark:text-slate-400 '
                'file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 '
                'file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 '
                'hover:file:bg-brand-100 dark:file:bg-slate-800 dark:file:text-slate-300 '
                'dark:hover:file:bg-slate-700 transition cursor-pointer'
            ),
            'accept': '.csv,.xlsx',
            'id': 'structure-file-input',
        })
    )


class FacultyMasterUploadForm(forms.Form):
    """Form to upload Faculty Master Excel/CSV file."""

    faculty_file = forms.FileField(
        label='Select Faculty List (CSV or Excel)',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])],
        widget=forms.FileInput(attrs={
            'class': (
                'block w-full text-sm text-slate-500 dark:text-slate-400 '
                'file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 '
                'file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 '
                'hover:file:bg-brand-100 dark:file:bg-slate-800 dark:file:text-slate-300 '
                'dark:hover:file:bg-slate-700 transition cursor-pointer'
            ),
            'accept': '.csv,.xlsx',
            'id': 'faculty-file-input',
        })
    )


class TeachingAllocationUploadForm(forms.Form):
    """Form to upload Teaching Allocation Excel/CSV file."""

    allocation_file = forms.FileField(
        label='Select Course Allocation File (CSV or Excel)',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])],
        widget=forms.FileInput(attrs={
            'class': (
                'block w-full text-sm text-slate-500 dark:text-slate-400 '
                'file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 '
                'file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 '
                'hover:file:bg-brand-100 dark:file:bg-slate-800 dark:file:text-slate-300 '
                'dark:hover:file:bg-slate-700 transition cursor-pointer'
            ),
            'accept': '.csv,.xlsx',
            'id': 'allocation-file-input',
        })
    )


class FacultyMasterEditForm(forms.ModelForm):
    """Form to edit a single FacultyMaster record."""

    class Meta:
        from apps.academic.models import FacultyMaster
        model = FacultyMaster
        fields = ['faculty_name', 'short_form', 'email', 'employee_code',
                  'department', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = (
            "mt-1 block w-full rounded-md border-slate-300 shadow-sm "
            "focus:border-brand-500 focus:ring-brand-500 sm:text-sm "
            "dark:bg-slate-800 dark:border-slate-700 dark:text-white"
        )
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (
                    "rounded border-slate-300 text-brand-600 shadow-sm "
                    "focus:ring-brand-500 dark:bg-slate-800 dark:border-slate-700"
                )
            else:
                field.widget.attrs['class'] = input_class
