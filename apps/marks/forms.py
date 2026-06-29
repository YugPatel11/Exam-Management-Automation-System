"""
Forms for Marks Entry.
"""
from django import forms
from apps.marks.models import StudentMark


class CsvUploadForm(forms.Form):
    """
    Form for uploading marks via CSV.
    """
    file = forms.FileField(
        label="Select CSV File",
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 dark:file:bg-brand-900/50 dark:file:text-brand-300 dark:hover:file:bg-brand-900',
            'accept': '.csv'
        })
    )


class DynamicMarksEntryForm(forms.ModelForm):
    """
    Dynamically generates fields based on the assessment scheme components.
    """
    class Meta:
        model = StudentMark
        fields = ['status']

    def __init__(self, *args, **kwargs):
        self.components = kwargs.pop('components', [])
        super().__init__(*args, **kwargs)
        
        self.fields['status'].widget.attrs.update({'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm'})
        
        # Add dynamic fields for each component
        for comp in self.components:
            field_name = comp['key']
            max_marks = comp['max_marks']
            
            # Get existing value if instance exists
            initial_val = None
            if self.instance.pk and self.instance.component_marks:
                initial_val = self.instance.component_marks.get(field_name)
                
            self.fields[field_name] = forms.IntegerField(
                min_value=0,
                required=False, # Not required if absent/ufm
                initial=initial_val,
                widget=forms.NumberInput(attrs={
                    'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm marks-input',
                    'placeholder': 'Marks'
                })
            )

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status', 'Present')
        
        if status in ['AB', 'UFM']:
            for comp in self.components:
                cleaned_data[comp['key']] = 0
        else:
            # Validate required marks
            for comp in self.components:
                val = cleaned_data.get(comp['key'])
                if val is None:
                    self.add_error(comp['key'], "This field is required if student is present.")
                    
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Save dynamic fields into JSONField
        marks_dict = {}
        total = 0
        
        for comp in self.components:
            key = comp['key']
            val = self.cleaned_data.get(key, 0)
            marks_dict[key] = float(val) if val else 0
            total += float(val) if val else 0
            
        instance.component_marks = marks_dict
        instance.total_marks = total
        
        if commit:
            instance.save()
            
        return instance
