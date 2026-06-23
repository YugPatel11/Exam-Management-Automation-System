from datetime import timedelta
from apps.scheduling.models import ExamSchedule
from apps.curriculum.models import CurriculumMapping
from apps.master_data.models import Subject

class ScheduleGeneratorService:
    """
    Generates exam schedules by grouping subjects by Program and Semester.
    Skips Sundays and locked records.
    """
    def __init__(self, exam, start_time, end_time):
        self.exam = exam
        self.start_time = start_time
        self.end_time = end_time
        self.errors = []
        self.scheduled_count = 0
        self.skipped_count = 0

    def generate(self):
        # Clear existing unlocked schedules for this exam
        ExamSchedule.objects.filter(exam=self.exam, is_locked=False).delete()
        
        locked_schedules = ExamSchedule.objects.filter(exam=self.exam, is_locked=True)
        locked_subject_ids = set(locked_schedules.values_list('subject_id', flat=True))

        # Get all programs linked to this exam
        programs = self.exam.programs.all()
        if not programs:
            self.errors.append("No programs are associated with this exam.")
            return

        # Fetch Curriculum Mappings for these programs
        mappings = CurriculumMapping.objects.filter(
            program__in=programs,
            subject__assessment_scheme__theory_ese__gt=0
        ).select_related('subject', 'program')

        # Group by Program and Semester
        groups = {}
        for m in mappings:
            if m.subject.id in locked_subject_ids:
                self.skipped_count += 1
                continue
                
            key = (m.program.id, m.semester)
            if key not in groups:
                groups[key] = []
            
            # Avoid duplicate subjects within the same program/semester if mapped weirdly
            if m.subject not in groups[key]:
                groups[key].append(m.subject)

        new_schedules = []
        
        # Schedule each group sequentially
        for (prog_id, sem), subjects in groups.items():
            current_date = self.exam.start_date
            
            for subject in subjects:
                # Find next available valid date
                while True:
                    if current_date > self.exam.end_date:
                        self.errors.append(f"Not enough days to schedule all subjects for Program ID {prog_id}, Semester {sem}.")
                        break
                    
                    # Skip Sundays (weekday() == 6)
                    if current_date.weekday() == 6:
                        current_date += timedelta(days=1)
                        continue
                        
                    break # Found a valid date
                
                if current_date > self.exam.end_date:
                    break # Stop scheduling this group if we ran out of days
                    
                # We need to make sure we don't accidentally schedule the SAME subject twice
                # if it belongs to multiple programs.
                # If it's already scheduled for this exam on a DIFFERENT date, that's a conflict.
                # But for simplicity, we just check if it's already in the new_schedules list.
                # If a subject is shared across programs, we should really just schedule it once.
                
                existing = [s for s in new_schedules if s.subject_id == subject.id]
                if existing:
                    # It's already scheduled (shared subject), skip adding a duplicate.
                    pass
                else:
                    new_schedules.append(ExamSchedule(
                        exam=self.exam,
                        subject=subject,
                        date=current_date,
                        start_time=self.start_time,
                        end_time=self.end_time,
                        is_locked=False
                    ))
                    self.scheduled_count += 1
                
                # Increment date for the next subject in this semester group
                current_date += timedelta(days=1)

        if new_schedules:
            ExamSchedule.objects.bulk_create(new_schedules)

        return len(new_schedules)
