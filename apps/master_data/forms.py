"""
Forms for Master Data management.
"""
from django import forms
from apps.master_data.models import Program, Subject, Division, Classroom


class BaseTailwindModelForm(forms.ModelForm):
    """
    Base form that applies standard Tailwind CSS classes to fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Add base classes
            classes = "mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm dark:bg-slate-800 dark:border-slate-700 dark:text-white"
            
            # Additional classes for specific widgets
            if isinstance(field.widget, forms.CheckboxInput):
                classes = "h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-800 dark:checked:bg-brand-500"
            elif isinstance(field.widget, forms.Select):
                classes += " bg-white dark:bg-slate-800"

            field.widget.attrs['class'] = classes


class ProgramForm(BaseTailwindModelForm):
    class Meta:
        model = Program
        fields = ['code', 'name', 'is_archived']
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'e.g., CE, ME, EE'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Computer Engineering'}),
        }


class SubjectForm(BaseTailwindModelForm):
    class Meta:
        model = Subject
        fields = ['code', 'name', 'is_archived']
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'e.g., CE101'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Data Structures'}),
        }


class DivisionForm(BaseTailwindModelForm):
    class Meta:
        model = Division
        fields = ['program', 'semester', 'name', 'is_archived']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., A, B, C'}),
        }


class ClassroomForm(BaseTailwindModelForm):
    class Meta:
        model = Classroom
        fields = ['room_number', 'capacity', 'is_archived']
        widgets = {
            'room_number': forms.TextInput(attrs={'placeholder': 'e.g., A-101, Lab-3'}),
        }
