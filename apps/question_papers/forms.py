"""
Forms for Question Papers.
"""
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from apps.question_papers.models import QuestionPaper, Question, QuestionPaperTemplate

class QuestionPaperTemplateForm(forms.ModelForm):
    class Meta:
        model = QuestionPaperTemplate
        fields = ['name', 'header_html', 'is_active']
        widgets = {
            'header_html': forms.Textarea(attrs={'class': 'tinymce'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['name']:
            self.fields[field].widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm'})

class QuestionPaperForm(forms.ModelForm):
    class Meta:
        model = QuestionPaper
        fields = ['exam', 'subject', 'program', 'semester', 'assessment_component', 'date', 'start_time', 'end_time', 'instructions']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'instructions': forms.Textarea(attrs={'rows': 3, 'class': 'invisible-input auto-resize'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['instructions', 'exam', 'program']:
                field.widget.attrs.update({'class': 'invisible-input text-center'})
                
        # Auto-create B.Tech program and hide field so user doesn't need to select it
        try:
            from apps.master_data.models import Program
            btech_program, created = Program.objects.get_or_create(
                code="B.Tech", 
                defaults={"name": "Bachelor of Technology"}
            )
            self.fields['program'].initial = btech_program
            self.fields['program'].widget = forms.HiddenInput()
        except Exception:
            pass


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_number', 'text', 'marks', 'co_mapping', 'btl_mapping', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'invisible-input auto-resize', 'rows': 2, 'placeholder': 'Enter question text...'}),
            'question_number': forms.TextInput(attrs={'class': 'invisible-input text-center'}),
            'marks': forms.NumberInput(attrs={'class': 'invisible-input text-center', 'readonly': 'readonly'}),
            'co_mapping': forms.Select(attrs={'class': 'invisible-input text-center'}),
            'btl_mapping': forms.Select(attrs={'class': 'invisible-input text-center'}),
            'order': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hardcode initial value if adding
        if not self.instance.pk:
            self.fields['marks'].initial = 5


class ExactSixQuestionsFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        
        # Count non-deleted forms
        valid_forms = 0
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if form.cleaned_data:
                valid_forms += 1
                
        if valid_forms != 6:
            raise forms.ValidationError("You must provide exactly 6 questions.")

QuestionFormSet = inlineformset_factory(
    QuestionPaper, Question, form=QuestionForm,
    formset=ExactSixQuestionsFormSet,
    extra=6, max_num=6, min_num=6, validate_min=True, validate_max=True, can_delete=False
)
