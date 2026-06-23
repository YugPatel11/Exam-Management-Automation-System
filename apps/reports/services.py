"""
Services for Reports Generation.
"""
import csv
import io
from django.db import transaction

from apps.reports.models import Report
from apps.core.models_audit import TextContent

from apps.seating.models import SeatingAllocation
from apps.duty_chart.models import DutyAssignment
from apps.marks.models import StudentMark
from apps.analysis.services import AnalysisService


class ReportGeneratorService:
    def __init__(self, exam, user):
        self.exam = exam
        self.user = user

    def _save_report(self, report_type, content_text, format_type='csv'):
        """Saves or updates a report and its TextContent."""
        with transaction.atomic():
            report = Report.objects.filter(exam=self.exam, report_type=report_type).first()
            if report:
                # Update existing text content
                report.content.text = content_text
                report.content.save()
                report.generated_by = self.user
                report.save()
            else:
                # Create new
                content = TextContent.objects.create(
                    module=f"reports_{report_type}",
                    identifier=f"exam_{self.exam.id}_{report_type}",
                    text=content_text
                )
                report = Report.objects.create(
                    exam=self.exam,
                    report_type=report_type,
                    content=content,
                    generated_by=self.user
                )
            return report

    def generate_seating_arrangement(self):
        """Generates a CSV text report of seating arrangements."""
        allocations = SeatingAllocation.objects.filter(plan__exam=self.exam).select_related(
            'schedule__subject', 'classroom', 'student'
        ).order_by('schedule__date', 'classroom__room_number', 'seat_number')
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Start Time', 'End Time', 'Subject', 'Classroom', 'Seat No', 'Student Roll No', 'Student Name'])
        
        for a in allocations:
            writer.writerow([
                a.schedule.date,
                a.schedule.start_time,
                a.schedule.end_time,
                a.schedule.subject.code,
                a.classroom.room_number,
                a.seat_number,
                a.student.roll_no,
                a.student.name
            ])
            
        return self._save_report('seating_arrangement', output.getvalue())

    def generate_duty_chart(self):
        """Generates a CSV text report of duty chart."""
        assignments = DutyAssignment.objects.filter(chart__exam=self.exam).select_related(
            'classroom', 'faculty'
        ).order_by('date', 'start_time', 'classroom__room_number')
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Start Time', 'End Time', 'Classroom', 'Faculty Name', 'Faculty Role'])
        
        for a in assignments:
            writer.writerow([
                a.date,
                a.start_time,
                a.end_time,
                a.classroom.room_number,
                a.faculty.get_display_name(),
                a.faculty.get_role_display()
            ])
            
        return self._save_report('duty_chart', output.getvalue())

    def generate_marks_summary(self):
        """Generates a CSV text report of marks."""
        marks = StudentMark.objects.filter(task__exam=self.exam, task__status='locked').select_related(
            'student', 'task__subject'
        ).order_by('task__subject__code', 'student__roll_no')
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Subject Code', 'Student Roll No', 'Student Name', 'Absent', 'Total Marks', 'Component Details'])
        
        for m in marks:
            writer.writerow([
                m.task.subject.code,
                m.student.roll_no,
                m.student.name,
                'Yes' if m.is_absent else 'No',
                m.total_marks,
                str(m.component_marks)
            ])
            
        return self._save_report('marks_summary', output.getvalue())

    def generate_result_analysis(self):
        """Generates a CSV text report of analysis."""
        service = AnalysisService(self.exam)
        prog_data = service.get_program_analysis()
        subj_data = service.get_subject_analysis()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['--- PROGRAM ANALYSIS ---'])
        writer.writerow(['Program', 'Average Marks', 'Pass Percentage'])
        for p in prog_data:
            writer.writerow([p['program'], p['average'], f"{p['pass_percentage']}%"])
            
        writer.writerow([])
        writer.writerow(['--- SUBJECT ANALYSIS ---'])
        writer.writerow(['Subject', 'Average Marks'])
        for s in subj_data:
            writer.writerow([s['subject'], s['average']])
            
        return self._save_report('result_analysis', output.getvalue())
