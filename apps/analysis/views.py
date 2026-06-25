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
