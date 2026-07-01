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
        
        context = {
            'subject': semester_subject.subject,
            'semester_subject': semester_subject,
            'parent_type': component.slug,
            'parent_type_display': component.name,
            'parent_max_marks': max_marks,
            'components': sub_components,
            'component': component
        }
        return render(request, 'assessment/builder.html', context)

    def post(self, request, component_id):
        component = get_object_or_404(MarksComponent, id=component_id)
        semester_subject = component.semester_subject
        
        # Verify access
        if not request.user.is_admin_role:
            is_coordinator = FacultyTeachingAssignment.objects.filter(
                faculty__user=request.user,
                semester_subject=semester_subject,
                is_coordinator=True
            ).exists()
            if not is_coordinator:
                messages.error(request, "Unauthorized.")
                return redirect('assessment:dashboard')

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

        # Validate that the sum of components does not exceed the parent max marks
        total_component_marks = sum(variables_dict.values())
        if total_component_marks > parent_max_marks:
            return self._json_response(False, f"Total component marks ({total_component_marks}) cannot exceed the parent max marks ({parent_max_marks}).")

        # Save to DB
        MarksSubComponent.objects.filter(marks_component=component).delete()
        
        new_components = []
        for i, c in enumerate(components_data):
            new_components.append(MarksSubComponent(
                marks_component=component,
                name=str(c.get('name', '')).strip(),
                max_marks=int(c.get('max_marks')),
                display_order=i
            ))
        MarksSubComponent.objects.bulk_create(new_components)

        return self._json_response(True, "Assessment Scheme configured successfully!")

    def _json_response(self, success, message):
        from django.http import JsonResponse
        return JsonResponse({'success': success, 'message': message})
