"""
Views for Result Analysis.
"""
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView
import json

from apps.core.mixins import RoleRequiredMixin
from apps.exams.models import Exam
from apps.analysis.services import analysis_service


class AnalysisDashboardView(RoleRequiredMixin, ListView):
    """
    List of Exams to view analysis for.
    Available to Admin, Exam Coordinator, and Subject Coordinator.
    """
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator']
    model = Exam
    template_name = 'analysis/dashboard.html'
    context_object_name = 'exams'


class ProgramAnalysisView(RoleRequiredMixin, View):
    """
    Shows Program-wise analysis for an exam.
    """
    allowed_roles = ['admin', 'exam_coordinator']
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        service = analysis_service(exam)
        
        program_data = service.get_program_analysis()
        
        # Prepare chart data
        labels = [d['program'] for d in program_data]
        averages = [d['average'] for d in program_data]
        pass_pcts = [d['pass_percentage'] for d in program_data]
        
        context = {
            'exam': exam,
            'program_data': program_data,
            'chart_labels': json.dumps(labels),
            'chart_averages': json.dumps(averages),
            'chart_pass_pcts': json.dumps(pass_pcts),
        }
        return render(request, 'analysis/program.html', context)


class SubjectAnalysisView(RoleRequiredMixin, View):
    """
    Shows Subject-wise analysis for an exam.
    """
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator']
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        service = analysis_service(exam)
        
        subject_data = service.get_subject_analysis()
        
        # Prepare chart data
        labels = [d['subject'] for d in subject_data]
        averages = [d['average'] for d in subject_data]
        
        context = {
            'exam': exam,
            'subject_data': subject_data,
            'chart_labels': json.dumps(labels),
            'chart_averages': json.dumps(averages),
        }
        return render(request, 'analysis/subject.html', context)


class DivisionAnalysisView(RoleRequiredMixin, View):
    """
    Shows Division-wise analysis for an exam.
    """
    allowed_roles = ['admin', 'exam_coordinator']
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        service = analysis_service(exam)
        
        division_data = service.get_division_analysis()
        
        labels = [d['division'] for d in division_data]
        averages = [d['average'] for d in division_data]
        pass_pcts = [d['pass_percentage'] for d in division_data]
        
        context = {
            'exam': exam,
            'division_data': division_data,
            'chart_labels': json.dumps(labels),
            'chart_averages': json.dumps(averages),
            'chart_pass_pcts': json.dumps(pass_pcts),
        }
        return render(request, 'analysis/division.html', context)


class FacultyAnalysisView(RoleRequiredMixin, View):
    """
    Shows Faculty-wise marks analysis for an exam.
    """
    allowed_roles = ['admin', 'exam_coordinator']
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        service = analysis_service(exam)
        
        faculty_data = service.get_faculty_analysis()
        
        labels = [d['faculty'] for d in faculty_data]
        averages = [d['average'] for d in faculty_data]
        
        context = {
            'exam': exam,
            'faculty_data': faculty_data,
            'chart_labels': json.dumps(labels),
            'chart_averages': json.dumps(averages),
        }
        return render(request, 'analysis/faculty.html', context)


class ComponentAnalysisView(RoleRequiredMixin, View):
    """
    Shows Component-wise (Theory CE, ESE, Practical CE, ESE) analysis for an exam.
    """
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator']
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        service = analysis_service(exam)
        
        component_data = service.get_component_analysis()
        
        labels = [d['component'] for d in component_data]
        averages = [d['average'] for d in component_data]
        max_marks = [d['max_marks'] for d in component_data]
        
        context = {
            'exam': exam,
            'component_data': component_data,
            'chart_labels': json.dumps(labels),
            'chart_averages': json.dumps(averages),
            'chart_max_marks': json.dumps(max_marks),
        }
        return render(request, 'analysis/component.html', context)


class COAnalysisView(RoleRequiredMixin, View):
    """
    Shows CO-wise (Course Outcome) marks distribution for an exam.
    """
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator']
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        service = analysis_service(exam)
        
        co_data = service.get_co_analysis()
        
        labels = [d['co'] for d in co_data]
        marks = [d['total_marks_allocated'] for d in co_data]
        
        context = {
            'exam': exam,
            'co_data': co_data,
            'chart_labels': json.dumps(labels),
            'chart_marks': json.dumps(marks),
        }
        return render(request, 'analysis/co.html', context)


class BTLAnalysisView(RoleRequiredMixin, View):
    """
    Shows BTL-wise (Bloom's Taxonomy Level) marks distribution for an exam.
    """
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator']
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        service = analysis_service(exam)
        
        btl_data = service.get_btl_analysis()
        
        labels = [f"{d['btl']} ({d['btl_label']})" for d in btl_data]
        marks = [d['total_marks_allocated'] for d in btl_data]
        
        context = {
            'exam': exam,
            'btl_data': btl_data,
            'chart_labels': json.dumps(labels),
            'chart_marks': json.dumps(marks),
        }
        return render(request, 'analysis/btl.html', context)

class StudentMarksAnalyticsView(RoleRequiredMixin, View):
    """
    Student Marks Analytics Module with role-based access.
    Displays highest marks, lowest marks, and pass/fail analysis.
    """
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator', 'faculty']
    
    def get(self, request):
        from apps.marks.models import StudentMark
        from apps.academic.models import FacultyTeachingAssignment
        from django.db.models import Q
        from apps.analysis.services import StudentMarksAnalyticsService

        user = request.user
        
        # Base query for dropdown options based on role
        qs = StudentMark.objects.filter(task__status='locked')

        if not user.is_admin_role and not user.is_exam_coordinator:
            if user.is_subject_coordinator:
                assigned_subjects = FacultyTeachingAssignment.objects.filter(
                    faculty__user=user, is_coordinator=True
                ).values_list('semester_subject__subject_id', flat=True)
                
                qs = qs.filter(
                    Q(task__subject_id__in=assigned_subjects) | 
                    Q(task__faculty=user)
                )
            else:
                qs = qs.filter(task__faculty=user)

        # Get unique options for filters
        exams = []
        subjects = []
        divisions = []
        exam_types = []
        
        # Use a single database hit to get distinct combinations
        filter_data = qs.values(
            'task__exam__id', 'task__exam__name',
            'task__subject__id', 'task__subject__code', 'task__subject__name',
            'task__division__id', 'task__division__name',
            'task__sub_component__name', 'task__exam__exam_type'
        ).distinct()
        
        exam_set = set()
        subject_set = set()
        division_set = set()
        exam_types_set = set()
        
        has_ce = False
        
        for item in filter_data:
            if item['task__exam__id'] and item['task__exam__id'] not in exam_set:
                exams.append({'id': item['task__exam__id'], 'name': item['task__exam__name']})
                exam_set.add(item['task__exam__id'])
                
            if item['task__subject__id'] and item['task__subject__id'] not in subject_set:
                subjects.append({'id': item['task__subject__id'], 'name': f"{item['task__subject__code']} - {item['task__subject__name']}"})
                subject_set.add(item['task__subject__id'])
                
            if item['task__division__id'] and item['task__division__id'] not in division_set:
                divisions.append({'id': item['task__division__id'], 'name': item['task__division__name']})
                division_set.add(item['task__division__id'])
                
            sub_comp_name = item.get('task__sub_component__name')
            exam_type = item.get('task__exam__exam_type')
            display_name = sub_comp_name if sub_comp_name else exam_type
            if display_name and display_name not in exam_types_set:
                exam_types.append({'name': display_name})
                exam_types_set.add(display_name)
                
            if exam_type and 'CE' in exam_type:
                has_ce = True

        if has_ce and 'CE Marks' not in exam_types_set:
            exam_types.append({'name': 'CE Marks'})
            exam_types_set.add('CE Marks')

        # Selected filters
        filters = {
            'exam_id': request.GET.get('exam'),
            'subject_id': request.GET.get('subject'),
            'division_id': request.GET.get('division'),
            'exam_type': request.GET.get('exam_type'),
            'marks_gt': request.GET.get('marks_gt'),
        }

        has_locked_marks = qs.exists()
        
        if has_locked_marks:
            # Get analytics data
            analytics_data = StudentMarksAnalyticsService.get_student_marks_analytics(user, filters)
        else:
            analytics_data = None
        
        context = {
            'has_locked_marks': has_locked_marks,
            'analytics_data': analytics_data,
            'exams': exams,
            'subjects': subjects,
            'divisions': divisions,
            'exam_types': sorted(exam_types, key=lambda x: x['name']),
            'selected_exam': filters['exam_id'],
            'selected_subject': filters['subject_id'],
            'selected_division': filters['division_id'],
            'selected_exam_type': filters['exam_type'],
            'selected_marks_gt': filters['marks_gt'],
        }
        
        return render(request, 'analysis/student_marks.html', context)

