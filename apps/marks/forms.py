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
    Supports the Theory CE formula: ((Internal1 + Internal2) / 2) + FE
    """
    class Meta:
        model = StudentMark
        fields = ['status']

    def __init__(self, *args, **kwargs):
        self.components = kwargs.pop('components', [])  # list of field dicts
        self.use_theory_ce_formula = kwargs.pop('use_theory_ce_formula', False)
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
                max_value=max_marks if max_marks is not None else None,
                required=False, # Not required if absent/ufm
                initial=initial_val,
                widget=forms.NumberInput(attrs={
                    'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm marks-input',
                    'placeholder': 'Marks',
                    'max': max_marks if max_marks is not None else '',
                    'data-group': comp.get('group', ''),
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

        if self.use_theory_ce_formula:
            # Theory CE = ((Internal 1 + Internal 2) / 2) + FE
            # Group fields by their group slug
            group_totals = {}
            for comp in self.components:
                group = comp.get('group', '')
                val = marks_dict.get(comp['key'], 0)
                group_totals.setdefault(group, 0)
                group_totals[group] += val

            # Find internal groups (those with _q suffixed keys) and FE group
            internal_sums = []
            fe_sum = 0
            for comp in self.components:
                group = comp.get('group', '')
                # Already counted via group_totals
                pass

            # Identify internals vs FE from group names
            counted_groups = set()
            for comp in self.components:
                group = comp.get('group', '')
                if group in counted_groups:
                    continue
                counted_groups.add(group)
                group_lower = group.lower()
                group_val = group_totals.get(group, 0)
                if 'internal' in group_lower or 'exam' in group_lower or 'theory' in group_lower:
                    internal_sums.append(group_val)
                else:
                    fe_sum += group_val

            if len(internal_sums) >= 2:
                # Average of internals + FE
                avg_internals = sum(internal_sums) / len(internal_sums)
                total = avg_internals + fe_sum
            elif len(internal_sums) == 1:
                total = internal_sums[0] + fe_sum
            else:
                total = fe_sum
        else:
            # Standard: total = sum of all marks
            for comp in self.components:
                val = marks_dict.get(comp['key'], 0)
                total += val
            
        instance.component_marks = marks_dict
        instance.total_marks = total
        
        if commit:
            instance.save()
            
        return instance
