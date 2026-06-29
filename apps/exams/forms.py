"""
Forms for Exam Management.
"""
from django import forms
from apps.exams.models import Exam
from apps.academic.models import AcademicYear, Semester


class ExamForm(forms.ModelForm):
    """
    Form to create and update Exam records.
    Uses cascading dropdowns: Academic Year → Semester.
    """
    class Meta:
        model = Exam
        fields = [
            'academic_year_ref', 'semester_ref', 'name', 'exam_type', 'status',
            'start_date', 'end_date', 'marks_entry_start', 'marks_entry_end',
            'programs', 'is_archived'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Mid Semester 1'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'marks_entry_start': forms.DateTimeInput(attrs={
                'type': 'datetime-local'
            }),
            'marks_entry_end': forms.DateTimeInput(attrs={
                'type': 'datetime-local'
            }),
            'programs': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure Academic Year dropdown
        self.fields['academic_year_ref'].queryset = AcademicYear.objects.filter(
            status='active'
        ).order_by('-name')
        self.fields['academic_year_ref'].empty_label = "— Select Academic Year —"

        # Configure Semester dropdown (filtered by selected AY)
        if self.instance.pk and self.instance.academic_year_ref:
            self.fields['semester_ref'].queryset = Semester.objects.filter(
                academic_year=self.instance.academic_year_ref
            ).order_by('number')
        elif 'academic_year_ref' in self.data:
            try:
                ay_id = int(self.data.get('academic_year_ref'))
                self.fields['semester_ref'].queryset = Semester.objects.filter(
                    academic_year_id=ay_id
                ).order_by('number')
            except (ValueError, TypeError):
                self.fields['semester_ref'].queryset = Semester.objects.none()
        else:
            self.fields['semester_ref'].queryset = Semester.objects.none()

        self.fields['semester_ref'].empty_label = "— Select Semester —"

        # Apply Tailwind classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = "space-y-2 mt-2"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-800 dark:checked:bg-brand-500"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "mt-1 block w-full rounded-md border-slate-300 bg-white shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm dark:bg-slate-800 dark:border-slate-700 dark:text-white"
            else:
                field.widget.attrs['class'] = "mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm dark:bg-slate-800 dark:border-slate-700 dark:text-white"

        # Add data attribute for AJAX on academic year field
        self.fields['academic_year_ref'].widget.attrs['id'] = 'id_academic_year_ref'
        self.fields['semester_ref'].widget.attrs['id'] = 'id_semester_ref'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                self.add_error('end_date', 'End date cannot be earlier than start date.')

        # Sync legacy academic_year field
        ay_ref = cleaned_data.get('academic_year_ref')
        if ay_ref:
            self.instance.academic_year = ay_ref.name

        return cleaned_data
