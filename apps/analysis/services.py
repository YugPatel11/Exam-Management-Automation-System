"""
Services for Result Analysis.
"""
from django.db.models import Sum, Avg, Count, Max, Min
from collections import defaultdict
from apps.marks.models import StudentMark


class AnalysisService:
    def __init__(self, exam):
        self.exam = exam
        
    def get_program_analysis(self):
        """
        Returns average marks and pass percentage by program.
        """
        marks = StudentMark.objects.filter(task__exam=self.exam, task__status='locked').select_related('student__program')
        
        program_data = defaultdict(lambda: {'total_marks': 0, 'student_count': 0, 'pass_count': 0})
        
        for m in marks:
            prog_name = m.student.program.code
            program_data[prog_name]['total_marks'] += float(m.total_marks)
            program_data[prog_name]['student_count'] += 1
            
            # Simple pass criteria: > 40% (assume max 100 for now, or just some logic)
            # A real implementation would use the assessment scheme max_marks.
            if float(m.total_marks) >= 40:
                program_data[prog_name]['pass_count'] += 1
                
        results = []
        for prog, data in program_data.items():
            avg = data['total_marks'] / data['student_count'] if data['student_count'] > 0 else 0
            pass_pct = (data['pass_count'] / data['student_count']) * 100 if data['student_count'] > 0 else 0
            results.append({
                'program': prog,
                'average': round(avg, 2),
                'pass_percentage': round(pass_pct, 2)
            })
            
        return results

    def get_subject_analysis(self, program_id=None):
        """
        Returns average marks by subject.
        """
        qs = StudentMark.objects.filter(task__exam=self.exam, task__status='locked').select_related('task__subject')
        
        if program_id:
            qs = qs.filter(student__program_id=program_id)
            
        subject_data = defaultdict(lambda: {'total_marks': 0, 'student_count': 0})
        
        for m in qs:
            sub_code = m.task.subject.code
            subject_data[sub_code]['total_marks'] += float(m.total_marks)
            subject_data[sub_code]['student_count'] += 1
            
        results = []
        for sub, data in subject_data.items():
            avg = data['total_marks'] / data['student_count'] if data['student_count'] > 0 else 0
            results.append({
                'subject': sub,
                'average': round(avg, 2)
            })
            
        return results

analysis_service = AnalysisService
