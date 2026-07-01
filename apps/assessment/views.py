"""
Views for Assessment Scheme Configuration.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
import json

from apps.master_data.models import Subject
from apps.academic.models import SemesterSubject, FacultyTeachingAssignment, MarksComponent, MarksSubComponent
from apps.curriculum.models import AssessmentScheme
from apps.assessment.models import AssessmentComponent

class SubjectCoordinatorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_subject_coordinator or user.is_admin_role)


class CoordinatorDashboardView(SubjectCoordinatorRequiredMixin, ListView):
    """
    Shows a list of subjects assigned to the logged-in user as a Coordinator.
    """
    model = SemesterSubject
    template_name = 'assessment/dashboard.html'
    context_object_name = 'semester_subjects'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_role:
            return SemesterSubject.objects.all().select_related('subject', 'semester__academic_year')
        
        assigned_ss_ids = FacultyTeachingAssignment.objects.filter(
            faculty__user=user,
            is_coordinator=True
        ).values_list('semester_subject_id', flat=True)
        return SemesterSubject.objects.filter(id__in=assigned_ss_ids).select_related('subject', 'semester__academic_year')


class SchemeBuilderView(SubjectCoordinatorRequiredMixin, View):
    """
    Interactive form builder for assessment components.
    Handles dynamic UI and mathematical validation.
    """
    def get(self, request, component_id):
        component = get_object_or_404(MarksComponent, id=component_id)
        semester_subject = component.semester_subject
        comp_name_lower = component.name.lower()
        
        # Block Tutorial components — no sub-components allowed
        if comp_name_lower in ['tutorial ce', 'tutorial_ce', 'tutorial ese', 'tutorial_ese']:
            messages.error(request, "Tutorial components do not support sub-components. Marks are entered directly.")
            return redirect('assessment:dashboard')
        
        # Verify access
        if not request.user.is_admin_role:
            is_coordinator = FacultyTeachingAssignment.objects.filter(
                faculty__user=request.user,
                semester_subject=semester_subject,
                is_coordinator=True
            ).exists()
            if not is_coordinator:
                messages.error(request, "You are not assigned as the coordinator for this subject.")
                return redirect('assessment:dashboard')

        max_marks = component.max_marks
        if max_marks == 0:
            messages.error(request, "This component type is not applicable for this subject (Max Marks = 0).")
            return redirect('assessment:dashboard')

        sub_components = MarksSubComponent.objects.filter(marks_component=component).order_by('display_order')
        
        # Determine component-specific rules for the template
        is_theory_ce = comp_name_lower in ['theory ce', 'theory_ce']
        is_theory_ese = comp_name_lower in ['theory ese', 'theory_ese']
        is_practical = 'practical' in comp_name_lower
        
        context = {
            'subject': semester_subject.subject,
            'semester_subject': semester_subject,
            'parent_type': component.slug,
            'parent_type_display': component.name,
            'parent_max_marks': max_marks,
            'components': sub_components,
            'component': component,
            'is_theory_ce': is_theory_ce,
            'is_theory_ese': is_theory_ese,
            'is_practical': is_practical,
        }
        return render(request, 'assessment/builder.html', context)

    def post(self, request, component_id):
        component = get_object_or_404(MarksComponent, id=component_id)
        semester_subject = component.semester_subject
        comp_name_lower = component.name.lower()
        
        # Block Tutorial components
        if comp_name_lower in ['tutorial ce', 'tutorial_ce', 'tutorial ese', 'tutorial_ese']:
            return self._json_response(False, "Tutorial components do not support sub-components.")
        
        # Verify access
        if not request.user.is_admin_role:
            is_coordinator = FacultyTeachingAssignment.objects.filter(
                faculty__user=request.user,
                semester_subject=semester_subject,
                is_coordinator=True
            ).exists()
            if not is_coordinator:
                return self._json_response(False, "Unauthorized.")

        # Parent max marks
        parent_max_marks = component.max_marks

        # Parse submitted data
        try:
            raw_data = json.loads(request.body)
            components_data = raw_data.get('components', [])
        except json.JSONDecodeError:
            return self._json_response(False, "Invalid JSON data.")

        if not components_data:
            return self._json_response(False, "At least one component is required.")

        # Build variables dict for validation
        variables_dict = {}
        names_seen = set()
        
        for i, c in enumerate(components_data):
            c_name = str(c.get('name', '')).strip()
            v_marks = c.get('max_marks')
            
            if not c_name or v_marks is None or v_marks == '':
                return self._json_response(False, f"Component #{i+1} is missing a Name or Max Marks.")
                
            if c_name in names_seen:
                return self._json_response(False, f"Duplicate component name found: '{c_name}'")
                
            try:
                v_marks = int(v_marks)
            except ValueError:
                return self._json_response(False, f"Max Marks for '{c_name}' must be an integer.")
                
            variables_dict[c_name] = v_marks
            names_seen.add(c_name)

        # Validate total — must EQUAL parent max marks (not just "not exceed")
        total_component_marks = sum(variables_dict.values())
        
        is_theory_ce = comp_name_lower in ['theory ce', 'theory_ce']
        
        if is_theory_ce:
            # Theory CE special validation:
            # Internal 1 and Internal 2 must each be 30 marks
            internal_count = 0
            internal_total = 0
            non_internal_total = 0
            for c_name, c_marks in variables_dict.items():
                c_lower = c_name.lower()
                if 'internal' in c_lower or 'exam' in c_lower:
                    internal_count += 1
                    internal_total += c_marks
                    if c_marks != 30:
                        return self._json_response(
                            False,
                            f"'{c_name}' must have exactly 30 marks (6 questions × 5 marks each)."
                        )
                else:
                    non_internal_total += c_marks
            
            if internal_count < 2:
                return self._json_response(
                    False,
                    "Theory CE requires at least 2 internal/exam components (e.g., Internal 1 and Internal 2), each with 30 marks."
                )
            
            # Validate formula result: ((sum_internals / count) + non_internal) must equal parent max
            formula_result = (internal_total / internal_count) + non_internal_total
            if formula_result != parent_max_marks:
                return self._json_response(
                    False,
                    f"Formula result ({formula_result:.0f}) must equal target max marks ({parent_max_marks}). "
                    f"Formula: ((Internal total {internal_total}) / {internal_count}) + FE ({non_internal_total}) = {formula_result:.0f}"
                )
        else:
            # All other types: total must equal parent max marks
            if total_component_marks != parent_max_marks:
                return self._json_response(
                    False,
                    f"Total component marks ({total_component_marks}) must equal the parent max marks ({parent_max_marks})."
                )

        # Save to DB
        MarksSubComponent.objects.filter(marks_component=component).delete()
        
        from django.utils.text import slugify
        new_components = []
        for i, c in enumerate(components_data):
            c_name = str(c.get('name', '')).strip()
            c_lower = c_name.lower()
            
            # For Theory CE internals, force 6 questions
            num_questions = int(c.get('number_of_questions', 1))
            if is_theory_ce and ('internal' in c_lower or 'exam' in c_lower):
                num_questions = 6
            
            new_components.append(MarksSubComponent(
                marks_component=component,
                name=c_name,
                slug=slugify(c_name).replace('-', '_'),
                max_marks=int(c.get('max_marks')),
                number_of_questions=num_questions,
                display_order=i
            ))
        MarksSubComponent.objects.bulk_create(new_components)
        
        # Regenerate Marks Entry Tasks for this component to reflect sub-component split
        from apps.marks.models import MarksEntryTask
        from apps.exams.services import ExamAutoGenerationService
        
        # Delete old tasks for this subject/component that are pending
        MarksEntryTask.objects.filter(
            exam__exam_type=component.name,
            subject=component.semester_subject.subject,
            status='pending'
        ).delete()
        
        # Regenerate
        ay = component.semester_subject.semester.academic_year
        ExamAutoGenerationService.generate_exams_for_academic_year(ay)

        return self._json_response(True, "Assessment Scheme configured successfully!")

    def _json_response(self, success, message):
        from django.http import JsonResponse
        return JsonResponse({'success': success, 'message': message})
