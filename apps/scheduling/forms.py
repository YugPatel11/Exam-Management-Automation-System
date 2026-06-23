"""
Forms for Exam Scheduling.
"""
from django import forms
from apps.scheduling.models import ExamSchedule

class AutoGenerateForm(forms.Form):
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white',
        }),
        label="Default Start Time",
        initial="10:00"
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white',
        }),
        label="Default End Time",
        initial="13:00"
    )

class ExamScheduleEditForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'block w-full border-slate-300 dark:border-slate-700 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-slate-800 dark:text-white'}),
        }
