"""
Models for Marks Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Subject, Division


class MarksEntryTask(BaseModel):
    """
    Represents a task assigned to a faculty member to enter marks for a subject/division.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Entry'),
        ('in_progress', 'Draft / In Progress'),
        ('submitted', 'Submitted for Review'),
        ('locked', 'Locked / Finalized'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks_tasks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks_tasks')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='marks_tasks', null=True, blank=True)
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marks_tasks')

    # ──── New: Link to SemesterSubject for dynamic marks components ────
    semester_subject = models.ForeignKey(
        'academic.SemesterSubject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marks_tasks',
        verbose_name="Semester Subject",
        help_text="Links this task to the academic structure for dynamic marks components."
    )
    
    sub_component = models.ForeignKey(
        'academic.MarksSubComponent',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='marks_tasks',
        verbose_name="Marks Sub-Component",
        help_text="If this task is specifically for a sub-component like Internal 1."
    )
    
    teaching_assignment = models.ForeignKey(
        'academic.FacultyTeachingAssignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marks_tasks',
        verbose_name="Teaching Assignment",
        help_text="Links this task to the specific class and batch assignment."
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('exam', 'subject', 'division', 'teaching_assignment', 'faculty', 'sub_component')
        verbose_name = "Marks Entry Task"
        verbose_name_plural = "Marks Entry Tasks"

    def __str__(self):
        suffix = f" - {self.sub_component.name}" if self.sub_component else ""
        if self.teaching_assignment:
            return f"{self.subject.code} - {self.teaching_assignment.class_name}{suffix} ({self.faculty.get_display_name()})"
        div_code = self.division.name if self.division else "All"
        return f"{self.subject.code} - {div_code}{suffix} ({self.faculty.get_display_name()})"

    def get_marks_components(self):
        """
        Returns the marks entry fields for this task.
        
        Returns a dict with:
            'fields': list of {'key', 'label', 'max_marks', 'group'} dicts
            'component_type': str  (e.g., 'theory_ce', 'practical_ese')
            'has_sub_components': bool
            'use_theory_ce_formula': bool  — if True, total = ((I1+I2)/2) + FE
            'parent_max_marks': int
        """
        if self.semester_subject:
            return self._get_components_from_academic_structure()
        else:
            return self._get_components_legacy()

    def _get_components_from_academic_structure(self):
        from apps.academic.models import MarksComponent, MarksSubComponent

        exam_component_name = self.exam.exam_type
        result = {
            'fields': [],
            'component_type': '',
            'has_sub_components': False,
            'use_theory_ce_formula': False,
            'parent_max_marks': 0,
        }

        mc_qs = MarksComponent.objects.filter(
            semester_subject=self.semester_subject,
            max_marks__gt=0,
            name=exam_component_name
        ).order_by('display_order')

        for mc in mc_qs:
            comp_type = mc.slug  # e.g. theory_ce, practical_ese
            comp_name_lower = mc.name.lower()
            result['component_type'] = comp_type
            result['parent_max_marks'] = mc.max_marks
            
            if self.sub_component:
                result['parent_max_marks'] = self.sub_component.max_marks

            sub_comps = MarksSubComponent.objects.filter(
                marks_component=mc
            ).order_by('display_order')

            # ── Tutorial CE / ESE: never sub-components ──
            if comp_name_lower in ['tutorial ce', 'tutorial_ce',
                                    'tutorial ese', 'tutorial_ese']:
                result['fields'].append({
                    'key': mc.slug,
                    'label': mc.name,
                    'max_marks': mc.max_marks,
                    'group': mc.slug,
                })
                continue

            # ── Component WITH sub-components ──
            if sub_comps.exists():
                result['has_sub_components'] = True

                # Theory CE with sub-components → Internal 1/2 (6×5) + FE
                if comp_name_lower in ['theory ce', 'theory_ce']:
                    result['use_theory_ce_formula'] = True
                    for sc in sub_comps:
                        if self.sub_component and sc.id != self.sub_component.id:
                            continue
                        sc_lower = sc.name.lower()
                        is_internal = ('internal' in sc_lower or 'exam' in sc_lower
                                       or 'theory' in sc_lower)
                        if is_internal:
                            # Fixed: 6 questions × 5 marks
                            for i in range(1, 7):
                                result['fields'].append({
                                    'key': f"{sc.slug}_q{i}",
                                    'label': f"{sc.name} Q{i}",
                                    'max_marks': 5,
                                    'group': sc.slug,
                                })
                        else:
                            # e.g. Faculty Evaluation — single field
                            result['fields'].append({
                                'key': sc.slug,
                                'label': sc.name,
                                'max_marks': sc.max_marks,
                                'group': sc.slug,
                            })
                    continue

                # Theory ESE / Practical CE / Practical ESE with sub-components
                for sc in sub_comps:
                    if self.sub_component and sc.id != self.sub_component.id:
                        continue
                    result['fields'].append({
                        'key': sc.slug,
                        'label': sc.name,
                        'max_marks': sc.max_marks,
                        'group': sc.slug,
                    })
                continue

            # ── Component WITHOUT sub-components → direct entry ──
            result['fields'].append({
                'key': mc.slug,
                'label': mc.name,
                'max_marks': mc.max_marks,
                'group': mc.slug,
            })

        return result

    def _get_components_legacy(self):
        """Legacy fallback using AssessmentScheme."""
        result = {
            'fields': [],
            'component_type': '',
            'has_sub_components': False,
            'use_theory_ce_formula': False,
            'parent_max_marks': 0,
        }
        try:
            scheme = self.subject.assessment_scheme
        except Exception:
            return result

        exam_type_lower = self.exam.exam_type.lower() if self.exam.exam_type else ''

        if 'theory ce' in exam_type_lower or 'theory_ce' in exam_type_lower:
            result['component_type'] = 'theory_ce'
            result['parent_max_marks'] = scheme.theory_ce
            if scheme.theory_ce > 0:
                result['fields'].append({
                    'key': 'theory_ce',
                    'label': 'Theory CE',
                    'max_marks': scheme.theory_ce,
                    'group': 'theory_ce',
                })
        elif 'theory ese' in exam_type_lower or 'theory_ese' in exam_type_lower:
            result['component_type'] = 'theory_ese'
            result['parent_max_marks'] = scheme.theory_ese
            if scheme.theory_ese > 0:
                result['fields'].append({
                    'key': 'theory_ese',
                    'label': 'Theory ESE',
                    'max_marks': scheme.theory_ese,
                    'group': 'theory_ese',
                })
        elif 'practical ce' in exam_type_lower or 'practical_ce' in exam_type_lower:
            result['component_type'] = 'practical_ce'
            result['parent_max_marks'] = scheme.practical_ce
            if scheme.practical_ce > 0:
                result['fields'].append({
                    'key': 'practical_ce',
                    'label': 'Practical CE',
                    'max_marks': scheme.practical_ce,
                    'group': 'practical_ce',
                })
        elif 'practical ese' in exam_type_lower or 'practical_ese' in exam_type_lower:
            result['component_type'] = 'practical_ese'
            result['parent_max_marks'] = scheme.practical_ese
            if scheme.practical_ese > 0:
                result['fields'].append({
                    'key': 'practical_ese',
                    'label': 'Practical ESE',
                    'max_marks': scheme.practical_ese,
                    'group': 'practical_ese',
                })
        elif 'tutorial ce' in exam_type_lower or 'tutorial_ce' in exam_type_lower:
            result['component_type'] = 'tutorial_ce'
            result['parent_max_marks'] = scheme.tutorial_ce
            if scheme.tutorial_ce > 0:
                result['fields'].append({
                    'key': 'tutorial_ce',
                    'label': 'Tutorial CE',
                    'max_marks': scheme.tutorial_ce,
                    'group': 'tutorial_ce',
                })
        elif 'tutorial ese' in exam_type_lower or 'tutorial_ese' in exam_type_lower:
            result['component_type'] = 'tutorial_ese'
            result['parent_max_marks'] = scheme.tutorial_ese
            if scheme.tutorial_ese > 0:
                result['fields'].append({
                    'key': 'tutorial_ese',
                    'label': 'Tutorial ESE',
                    'max_marks': scheme.tutorial_ese,
                    'group': 'tutorial_ese',
                })

        return result


class StudentMark(BaseModel):
    """
    Represents the marks obtained by a student for a specific task.
    Component marks are stored dynamically in a JSONField based on the Assessment Scheme.
    """
    task = models.ForeignKey(MarksEntryTask, on_delete=models.CASCADE, related_name='student_marks')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='marks')
    
    # Store dynamic marks like {"theory_ce": 25, "theory_ese": 30, "practical_ce": 40}
    component_marks = models.JSONField(default=dict, blank=True)
    
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('AB', 'Absent'),
        ('UFM', 'Unfair Means'),
    ]
    
    # Computed totals
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')

    class Meta:
        unique_together = ('task', 'student')
        ordering = ['student__roll_no']
        verbose_name = "Student Mark"
        verbose_name_plural = "Student Marks"

    def __str__(self):
        return f"{self.student.roll_no} - {self.total_marks}"
