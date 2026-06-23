"""
Forms for Question Papers.
"""
from django import forms
from django.forms import inlineformset_factory
from apps.question_papers.models import QuestionPaper, Question

class QuestionPaperForm(forms.ModelForm):
    class Meta:
        model = QuestionPaper
        fields = ['exam', 'subject', 'program', 'semester', 'date', 'start_time', 'end_time', 'total_marks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm'})


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_number', 'text', 'marks', 'co_mapping', 'btl_mapping', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm'})
        
        self.fields['text'].widget.attrs.update({'rows': 2})


QuestionFormSet = inlineformset_factory(
    QuestionPaper, Question, form=QuestionForm,
    extra=1, can_delete=True
)
