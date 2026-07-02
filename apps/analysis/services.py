"""
Services for Result Analysis.
"""
from django.db.models import Sum, Avg, Count, Max, Min
from collections import defaultdict
from apps.marks.models import StudentMark


class AnalysisService:
    def __init__(self, exam):
        self.exam = exam
        self._locked_marks = None

    def _get_locked_marks(self):
        """Cached query for locked marks across the exam."""
        if self._locked_marks is None:
            self._locked_marks = StudentMark.objects.filter(
                task__exam=self.exam, task__status='locked'
            ).select_related('student__program', 'task__subject', 'task__faculty', 'task__division')
        return self._locked_marks

    def get_program_analysis(self):
        """
        Returns average marks and pass percentage by program.
        """
        marks = self._get_locked_marks()
        
        program_data = defaultdict(lambda: {'total_marks': 0, 'student_count': 0, 'pass_count': 0, 'max_possible': 0})
        
        for m in marks:
            prog_name = m.student.program.code
            total = float(m.total_marks)
            program_data[prog_name]['total_marks'] += total
            program_data[prog_name]['student_count'] += 1
            
            # Calculate max possible marks from assessment scheme
            try:
                scheme = m.task.subject.assessment_scheme
                max_marks = scheme.theory_ce + scheme.theory_ese + scheme.practical_ce + scheme.practical_ese
                if total >= (max_marks * 0.4):  # 40% pass criteria
                    program_data[prog_name]['pass_count'] += 1
                program_data[prog_name]['max_possible'] = max_marks
            except Exception:
                if total >= 40:
                    program_data[prog_name]['pass_count'] += 1
                
        results = []
        for prog, data in sorted(program_data.items()):
            avg = data['total_marks'] / data['student_count'] if data['student_count'] > 0 else 0
            pass_pct = (data['pass_count'] / data['student_count']) * 100 if data['student_count'] > 0 else 0
            results.append({
                'program': prog,
                'average': round(avg, 2),
                'pass_percentage': round(pass_pct, 2),
                'student_count': data['student_count'],
            })
            
        return results

    def get_subject_analysis(self, program_id=None):
        """
        Returns average marks by subject.
        """
        marks = self._get_locked_marks()
        qs = marks
        
        if program_id:
            qs = qs.filter(student__program_id=program_id)
            
        subject_data = defaultdict(lambda: {'total_marks': 0, 'student_count': 0, 'pass_count': 0, 'max_marks': 0, 'highest': 0, 'lowest': float('inf')})
        
        for m in qs:
            sub_code = m.task.subject.code
            total = float(m.total_marks)
            subject_data[sub_code]['total_marks'] += total
            subject_data[sub_code]['student_count'] += 1
            subject_data[sub_code]['highest'] = max(subject_data[sub_code]['highest'], total)
            subject_data[sub_code]['lowest'] = min(subject_data[sub_code]['lowest'], total)
            
            try:
                scheme = m.task.subject.assessment_scheme
                max_marks = scheme.theory_ce + scheme.theory_ese + scheme.practical_ce + scheme.practical_ese
                subject_data[sub_code]['max_marks'] = max_marks
                if total >= (max_marks * 0.4):
                    subject_data[sub_code]['pass_count'] += 1
            except Exception:
                if total >= 40:
                    subject_data[sub_code]['pass_count'] += 1
            
        results = []
        for sub, data in sorted(subject_data.items()):
            avg = data['total_marks'] / data['student_count'] if data['student_count'] > 0 else 0
            pass_pct = (data['pass_count'] / data['student_count']) * 100 if data['student_count'] > 0 else 0
            results.append({
                'subject': sub,
                'average': round(avg, 2),
                'student_count': data['student_count'],
                'highest': data['highest'],
                'lowest': data['lowest'] if data['lowest'] != float('inf') else 0,
                'pass_percentage': round(pass_pct, 2),
            })
            
        return results

    def get_division_analysis(self):
        """
        Returns average marks by division.
        """
        marks = self._get_locked_marks()
        
        division_data = defaultdict(lambda: {'total_marks': 0, 'student_count': 0, 'pass_count': 0})
        
        for m in marks:
            div_name = m.task.division.name if m.task.division else 'Unassigned'
            total = float(m.total_marks)
            division_data[div_name]['total_marks'] += total
            division_data[div_name]['student_count'] += 1
            
            try:
                scheme = m.task.subject.assessment_scheme
                max_marks = scheme.theory_ce + scheme.theory_ese + scheme.practical_ce + scheme.practical_ese
                if total >= (max_marks * 0.4):
                    division_data[div_name]['pass_count'] += 1
            except Exception:
                if total >= 40:
                    division_data[div_name]['pass_count'] += 1
            
        results = []
        for div, data in sorted(division_data.items()):
            avg = data['total_marks'] / data['student_count'] if data['student_count'] > 0 else 0
            pass_pct = (data['pass_count'] / data['student_count']) * 100 if data['student_count'] > 0 else 0
            results.append({
                'division': div,
                'average': round(avg, 2),
                'student_count': data['student_count'],
                'pass_percentage': round(pass_pct, 2),
            })
            
        return results

    def get_faculty_analysis(self):
        """
        Returns average marks by faculty who entered marks.
        """
        marks = self._get_locked_marks()
        
        faculty_data = defaultdict(lambda: {'total_marks': 0, 'student_count': 0, 'faculty_name': ''})
        
        for m in marks:
            fac = m.task.faculty
            fac_key = fac.id
            faculty_data[fac_key]['total_marks'] += float(m.total_marks)
            faculty_data[fac_key]['student_count'] += 1
            faculty_data[fac_key]['faculty_name'] = fac.get_display_name()
            
        results = []
        for fac_id, data in faculty_data.items():
            avg = data['total_marks'] / data['student_count'] if data['student_count'] > 0 else 0
            results.append({
                'faculty': data['faculty_name'],
                'average': round(avg, 2),
                'student_count': data['student_count'],
            })
            
        return sorted(results, key=lambda x: x['faculty'])

    def get_component_analysis(self):
        """
        Returns average marks per assessment component (Theory CE, Theory ESE, etc.).
        """
        marks = self._get_locked_marks()
        
        component_data = defaultdict(lambda: {'total': 0, 'count': 0, 'max_marks': 0})
        
        for m in marks:
            if m.component_marks:
                for key, val in m.component_marks.items():
                    component_data[key]['total'] += float(val) if val else 0
                    component_data[key]['count'] += 1
                    
        # Get max marks from assessment scheme
        try:
            subjects_seen = set()
            for m in marks:
                sub = m.task.subject
                if sub.id not in subjects_seen:
                    subjects_seen.add(sub.id)
                    scheme = sub.assessment_scheme
                    if scheme.theory_ce > 0:
                        component_data['theory_ce']['max_marks'] = max(component_data['theory_ce']['max_marks'], scheme.theory_ce)
                    if scheme.theory_ese > 0:
                        component_data['theory_ese']['max_marks'] = max(component_data['theory_ese']['max_marks'], scheme.theory_ese)
                    if scheme.practical_ce > 0:
                        component_data['practical_ce']['max_marks'] = max(component_data['practical_ce']['max_marks'], scheme.practical_ce)
                    if scheme.practical_ese > 0:
                        component_data['practical_ese']['max_marks'] = max(component_data['practical_ese']['max_marks'], scheme.practical_ese)
        except Exception:
            pass
                    
        COMPONENT_LABELS = {
            'theory_ce': 'Theory CE',
            'theory_ese': 'Theory ESE',
            'practical_ce': 'Practical CE',
            'practical_ese': 'Practical ESE',
            'tutorial_ce': 'Tutorial CE',
            'tutorial_ese': 'Tutorial ESE',
        }
        
        results = []
        for comp, data in component_data.items():
            avg = data['total'] / data['count'] if data['count'] > 0 else 0
            results.append({
                'component': COMPONENT_LABELS.get(comp, comp),
                'component_key': comp,
                'average': round(avg, 2),
                'student_count': data['count'],
                'max_marks': data['max_marks'],
            })
            
        return results

    def get_co_analysis(self):
        """
        Returns CO-wise (Course Outcome) marks distribution using question paper mappings.
        """
        from apps.question_papers.models import Question
        
        # Get all question papers for this exam's subjects
        co_data = defaultdict(lambda: {'total_marks': 0, 'question_count': 0, 'max_marks': 0})
        
        questions = Question.objects.filter(
            paper__exam=self.exam
        ).values('co_mapping', 'marks')
        
        for q in questions:
            co = (q['co_mapping'] or '').strip().upper()
            if co:
                co_data[co]['total_marks'] += q['marks']
                co_data[co]['question_count'] += 1
                co_data[co]['max_marks'] += q['marks']
                
        results = []
        for co, data in sorted(co_data.items()):
            results.append({
                'co': co,
                'total_marks_allocated': data['max_marks'],
                'question_count': data['question_count'],
            })
            
        return results

    def get_btl_analysis(self):
        """
        Returns BTL-wise (Bloom's Taxonomy Level) marks distribution using question paper mappings.
        """
        from apps.question_papers.models import Question
        
        BTL_LABELS = {
            'L1': 'Remember',
            'L2': 'Understand',
            'L3': 'Apply',
            'L4': 'Analyze',
            'L5': 'Evaluate',
            'L6': 'Create',
        }
        
        btl_data = defaultdict(lambda: {'total_marks': 0, 'question_count': 0})
        
        questions = Question.objects.filter(
            paper__exam=self.exam
        ).values('btl_mapping', 'marks')
        
        for q in questions:
            btl = (q['btl_mapping'] or '').strip().upper()
            if btl:
                btl_data[btl]['total_marks'] += q['marks']
                btl_data[btl]['question_count'] += 1
                
        results = []
        for btl, data in sorted(btl_data.items()):
            results.append({
                'btl': btl,
                'btl_label': BTL_LABELS.get(btl, btl),
                'total_marks_allocated': data['total_marks'],
                'question_count': data['question_count'],
            })
            
        return results


analysis_service = AnalysisService

class StudentMarksAnalyticsService:
    @staticmethod
    def get_student_marks_analytics(user, filters):
        from django.db.models import Q
        from apps.marks.models import StudentMark
        from apps.academic.models import FacultyTeachingAssignment

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

        exam_id = filters.get('exam_id')
        subject_id = filters.get('subject_id')
        division_id = filters.get('division_id')
        exam_type = filters.get('exam_type')
        marks_gt = filters.get('marks_gt')

        if exam_id:
            qs = qs.filter(task__exam_id=exam_id)
        if subject_id:
            qs = qs.filter(task__subject_id=subject_id)
        if division_id:
            qs = qs.filter(task__division_id=division_id)
        if exam_type:
            if exam_type == 'CE Marks':
                qs = qs.filter(task__exam__exam_type__icontains='CE')
            else:
                qs = qs.filter(Q(task__sub_component__name=exam_type) | Q(task__exam__exam_type=exam_type, task__sub_component__isnull=True))

        highest_marks = 0
        lowest_marks = float('inf')
        total_students = 0
        
        # We need a list to hold all marks for the distribution chart
        all_marks = []

        if exam_type == 'CE Marks':
            # Group by student and apply CE formula: ((Internal 1 + Internal 2) / 2) + FE
            student_data = {}
            for mark in qs:
                s_id = mark.student_id
                if s_id not in student_data:
                    student_data[s_id] = {'internals': [], 'fe': 0}
                    
                total = float(mark.total_marks)
                if mark.task.sub_component:
                    sc_name = mark.task.sub_component.name.lower()
                    if 'internal' in sc_name or 'exam' in sc_name or 'theory' in sc_name:
                        student_data[s_id]['internals'].append(total)
                    else:
                        student_data[s_id]['fe'] += total
                else:
                    # If it's a parent task or doesn't have sub components, just add to fe
                    student_data[s_id]['fe'] += total
            
            for s_id, data in student_data.items():
                internals = data['internals']
                fe = data['fe']
                
                if len(internals) >= 2:
                    calc_total = sum(internals) / len(internals) + fe
                elif len(internals) == 1:
                    calc_total = internals[0] + fe
                else:
                    calc_total = fe
                    
                if marks_gt and calc_total < float(marks_gt):
                    continue
                    
                all_marks.append(calc_total)
                if calc_total > highest_marks:
                    highest_marks = calc_total
                if calc_total < lowest_marks:
                    lowest_marks = calc_total
                total_students += 1

        else:
            for mark in qs:
                total = float(mark.total_marks)
                
                # Apply Marks Filter (>=)
                if marks_gt and total < float(marks_gt):
                    continue
                    
                all_marks.append(total)
                if total > highest_marks:
                    highest_marks = total
                if total < lowest_marks:
                    lowest_marks = total
                
                total_students += 1

        if lowest_marks == float('inf'):
            lowest_marks = 0
            
        # Create Marks Distribution Bar Chart Data
        # We will create bins like 0-10, 11-20... up to max rounded up to nearest 10
        distribution = {}
        if total_students > 0:
            max_bin = int((highest_marks // 10) * 10 + 10)
            # Initialize bins
            for i in range(0, max_bin, 10):
                range_label = f"{i}-{i+9}"
                distribution[range_label] = 0
                
            for m in all_marks:
                bin_start = int(m // 10) * 10
                range_label = f"{bin_start}-{bin_start+9}"
                if range_label in distribution:
                    distribution[range_label] += 1
                else:
                    distribution[range_label] = 1
        
        dist_labels = list(distribution.keys())
        dist_data = list(distribution.values())

        return {
            'highest_marks': highest_marks,
            'lowest_marks': lowest_marks,
            'total_students': total_students,
            'dist_labels': dist_labels,
            'dist_data': dist_data,
        }
