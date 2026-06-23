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
