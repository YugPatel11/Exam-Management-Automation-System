"""
Forms for Exam Management.
"""
from django import forms
from apps.exams.models import Exam


class ExamForm(forms.ModelForm):
    """
    Form to create and update Exam records.
    Uses Tailwind CSS styling via widget attrs.
    """
    class Meta:
        model = Exam
        fields = [
            'academic_year', 'name', 'exam_type', 'status', 
            'start_date', 'end_date', 'programs', 'is_archived'
        ]
        widgets = {
            'academic_year': forms.TextInput(attrs={
                'placeholder': 'e.g., 2023-24'
            }),
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Mid Semester 1'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'programs': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply Tailwind classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                # CheckboxSelectMultiple needs specific handling for its internal list
                # The classes are applied to the <ul> wrapper by default, but we'll manage individual checkboxes in template or via CSS
                field.widget.attrs['class'] = "space-y-2 mt-2"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-800 dark:checked:bg-brand-500"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "mt-1 block w-full rounded-md border-slate-300 bg-white shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm dark:bg-slate-800 dark:border-slate-700 dark:text-white"
            else:
                field.widget.attrs['class'] = "mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm dark:bg-slate-800 dark:border-slate-700 dark:text-white"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                self.add_error('end_date', 'End date cannot be earlier than start date.')
        
        return cleaned_data
