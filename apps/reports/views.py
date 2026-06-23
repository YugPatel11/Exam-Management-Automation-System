"""
Views for Reports Management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View
from django.http import HttpResponse

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.exams.models import Exam
from apps.reports.models import Report
from apps.reports.services import ReportGeneratorService


class ReportsDashboardView(ExamCoordinatorRequiredMixin, ListView):
    """
    List of Exams for Exam Coordinators to manage reports.
    """
    model = Exam
    template_name = 'reports/dashboard.html'
    context_object_name = 'exams'


class ReportManagerView(ExamCoordinatorRequiredMixin, View):
    """
    Manage reports for an exam.
    """
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        reports = Report.objects.filter(exam=exam)
        
        # Convert to dictionary for easier template access
        reports_dict = {r.report_type: r for r in reports}
        
        context = {
            'exam': exam,
            'reports': reports_dict,
            'report_types': Report.REPORT_TYPES
        }
        return render(request, 'reports/manager.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        action = request.POST.get('action')
        report_type = request.POST.get('report_type')
        
        if action == 'generate' and report_type:
            service = ReportGeneratorService(exam, request.user)
            
            try:
                if report_type == 'seating_arrangement':
                    service.generate_seating_arrangement()
                elif report_type == 'duty_chart':
                    service.generate_duty_chart()
                elif report_type == 'marks_summary':
                    service.generate_marks_summary()
                elif report_type == 'result_analysis':
                    service.generate_result_analysis()
                    
                messages.success(request, f"Successfully generated {dict(Report.REPORT_TYPES).get(report_type)} report.")
            except Exception as e:
                messages.error(request, f"Error generating report: {str(e)}")
                
        return redirect('reports:manager', exam_id=exam.id)


class ReportDownloadView(ExamCoordinatorRequiredMixin, View):
    """
    Downloads the text content of a report as a CSV file.
    """
    def get(self, request, report_id):
        report = get_object_or_404(Report, id=report_id)
        
        response = HttpResponse(
            report.content.text,
            content_type='text/csv'
        )
        response['Content-Disposition'] = f'attachment; filename="{report.exam.name}_{report.report_type}.csv"'
        return response
