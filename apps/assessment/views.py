"""
Views for Assessment Scheme Configuration.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
import json

from apps.master_data.models import Subject
from apps.curriculum.models import AssessmentScheme
from apps.assessment.models import AssessmentComponent, ComponentFormula
from apps.assessment.services import FormulaValidator

class SubjectCoordinatorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_subject_coordinator or user.is_admin_role)


class CoordinatorDashboardView(SubjectCoordinatorRequiredMixin, ListView):
    """
    Shows a list of subjects assigned to the logged-in user as a Coordinator.
    """
    model = Subject
    template_name = 'assessment/dashboard.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_role:
            return Subject.objects.all().select_related('assessment_scheme')
        
        assigned_ids = user.coordinated_subjects.values_list('subject_id', flat=True)
        return Subject.objects.filter(id__in=assigned_ids).select_related('assessment_scheme')


class SchemeBuilderView(SubjectCoordinatorRequiredMixin, View):
    """
    Interactive form builder for assessment components.
    Handles dynamic UI and mathematical validation.
    """
    def get(self, request, subject_id, parent_type):
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Verify access
        if not request.user.is_admin_role:
            is_coordinator = request.user.coordinated_subjects.filter(subject_id=subject.id).exists()
            if not is_coordinator:
                messages.error(request, "You are not assigned as the coordinator for this subject.")
                return redirect('assessment:dashboard')

        # Get parent max marks from Curriculum AssessmentScheme
        try:
            scheme = subject.assessment_scheme
            max_marks = getattr(scheme, parent_type)
        except AssessmentScheme.DoesNotExist:
            messages.error(request, "No assessment scheme configured for this subject.")
            return redirect('assessment:dashboard')
            
        if max_marks == 0:
            messages.error(request, "This component type is not applicable for this subject (Max Marks = 0).")
            return redirect('assessment:dashboard')

        components = AssessmentComponent.objects.filter(subject=subject, parent_type=parent_type)
        formula_obj = ComponentFormula.objects.filter(subject=subject, parent_type=parent_type).first()

        context = {
            'subject': subject,
            'parent_type': parent_type,
            'parent_type_display': dict(AssessmentComponent.PARENT_TYPE_CHOICES).get(parent_type, parent_type),
            'parent_max_marks': max_marks,
            'components': components,
            'formula_string': formula_obj.formula_string if formula_obj else ""
        }
        return render(request, 'assessment/builder.html', context)

    def post(self, request, subject_id, parent_type):
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Verify access
        if not request.user.is_admin_role:
            is_coordinator = request.user.coordinated_subjects.filter(subject_id=subject.id).exists()
            if not is_coordinator:
                messages.error(request, "Unauthorized.")
                return redirect('assessment:dashboard')

        # Parent max marks
        scheme = subject.assessment_scheme
        parent_max_marks = getattr(scheme, parent_type)

        # Parse submitted data
        try:
            raw_data = json.loads(request.body)
            components_data = raw_data.get('components', [])
            formula_string = raw_data.get('formula', '').strip()
        except json.JSONDecodeError:
            return self._json_response(False, "Invalid JSON data.")

        if not components_data:
            return self._json_response(False, "At least one component is required.")

        if not formula_string:
            return self._json_response(False, "Formula is required.")

        # Build variables dict for validation
        variables_dict = {}
        variable_names_seen = set()
        
        for c in components_data:
            v_name = str(c.get('variable_name', '')).strip()
            v_marks = c.get('max_marks')
            
            if not v_name or v_marks is None:
                return self._json_response(False, "All components must have a Variable Name and Max Marks.")
                
            if v_name in variable_names_seen:
                return self._json_response(False, f"Duplicate variable name found: '{v_name}'")
                
            try:
                v_marks = int(v_marks)
            except ValueError:
                return self._json_response(False, f"Max Marks for '{v_name}' must be an integer.")
                
            variables_dict[v_name] = v_marks
            variable_names_seen.add(v_name)

        # Validate Formula Math
        validator = FormulaValidator(formula_string, variables_dict)
        is_valid = validator.validate(parent_max_marks)

        if not is_valid:
            error_msg = "Formula Validation Failed:<br>" + "<br>".join(validator.errors)
            return self._json_response(False, error_msg)

        # Save to DB
        AssessmentComponent.objects.filter(subject=subject, parent_type=parent_type).delete()
        
        new_components = []
        for c in components_data:
            new_components.append(AssessmentComponent(
                subject=subject,
                parent_type=parent_type,
                name=str(c.get('name', '')).strip(),
                variable_name=str(c.get('variable_name', '')).strip(),
                max_marks=int(c.get('max_marks'))
            ))
        AssessmentComponent.objects.bulk_create(new_components)

        formula_obj, _ = ComponentFormula.objects.get_or_create(
            subject=subject,
            parent_type=parent_type,
            defaults={'formula_string': formula_string}
        )
        formula_obj.formula_string = formula_string
        formula_obj.save()

        return self._json_response(True, "Assessment Scheme configured successfully!")

    def _json_response(self, success, message):
        from django.http import JsonResponse
        return JsonResponse({'success': success, 'message': message})
