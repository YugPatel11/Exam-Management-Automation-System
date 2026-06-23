import csv
import io
from django.db import transaction
from apps.master_data.models import Program, Subject
from apps.curriculum.models import AssessmentScheme, CurriculumMapping

class CurriculumImportService:
    """
    Handles CSV parsing, validation, and importing of Curriculum and Schemes.
    Auto-creates missing Subjects and Programs.
    """
    
    EXPECTED_COLUMNS = [
        'Course Code', 'Course Title', 'Program', 'Semester',
        'Theory CE', 'Theory ESE', 'Practical CE', 'Practical ESE',
        'Tutorial CE', 'Tutorial ESE'
    ]

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.errors = []
        self.valid_rows = []
        
        # Caches
        self.programs_cache = {p.code.upper(): p for p in Program.objects.all()}
        self.subjects_cache = {s.code.upper(): s for s in Subject.objects.all()}

    def validate_file(self):
        try:
            decoded_file = self.file_obj.read().decode('utf-8', errors='replace')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
            missing_cols = [col for col in self.EXPECTED_COLUMNS if col not in headers]
            if missing_cols:
                self.errors.append({
                    'row': 0,
                    'message': f"Missing required columns: {', '.join(missing_cols)}"
                })
                return self._get_summary()

            for row_idx, row in enumerate(reader, start=1):
                self._validate_row(row_idx, row)
                
        except Exception as e:
            self.errors.append({
                'row': 0,
                'message': f"Failed to parse CSV: {str(e)}"
            })
            
        return self._get_summary()

    def _safe_int(self, value):
        if not value or str(value).strip() == '':
            return 0
        try:
            return int(float(str(value).strip()))
        except ValueError:
            return None

    def _validate_row(self, row_idx, row):
        data = {k: str(v).strip() if v else '' for k, v in row.items()}
        
        course_code = data.get('Course Code')
        course_title = data.get('Course Title')
        program_code = data.get('Program')
        semester_str = data.get('Semester')
        
        if not all([course_code, course_title, program_code, semester_str]):
            self.errors.append({
                'row': row_idx,
                'course_code': course_code or 'Unknown',
                'message': "Missing one or more required fields (Course Code, Course Title, Program, Semester)."
            })
            return

        try:
            semester = int(semester_str)
        except ValueError:
            self.errors.append({
                'row': row_idx,
                'course_code': course_code,
                'message': f"Invalid Semester '{semester_str}'. Must be an integer."
            })
            return

        # Auto-create Program
        program = self.programs_cache.get(program_code.upper())
        if not program:
            program, _ = Program.objects.get_or_create(
                code=program_code.upper(),
                defaults={'name': program_code}
            )
            self.programs_cache[program_code.upper()] = program

        # Auto-create Subject
        subject = self.subjects_cache.get(course_code.upper())
        if not subject:
            subject, _ = Subject.objects.get_or_create(
                code=course_code.upper(),
                defaults={'name': course_title}
            )
            self.subjects_cache[course_code.upper()] = subject

        # Parse marks
        marks = {
            'theory_ce': self._safe_int(data.get('Theory CE')),
            'theory_ese': self._safe_int(data.get('Theory ESE')),
            'practical_ce': self._safe_int(data.get('Practical CE')),
            'practical_ese': self._safe_int(data.get('Practical ESE')),
            'tutorial_ce': self._safe_int(data.get('Tutorial CE')),
            'tutorial_ese': self._safe_int(data.get('Tutorial ESE')),
        }
        
        if None in marks.values():
            self.errors.append({
                'row': row_idx,
                'course_code': course_code,
                'message': "Invalid marks format. Must be an integer or blank."
            })
            return

        self.valid_rows.append({
            'row': row_idx,
            'subject_id': subject.id,
            'course_code': subject.code,
            'course_title': subject.name,
            'program_id': program.id,
            'program_code': program.code,
            'semester': semester,
            **marks
        })

    def _get_summary(self):
        return {
            'total_valid': len(self.valid_rows),
            'total_errors': len(self.errors),
            'errors': self.errors[:100],
            'valid_sample': self.valid_rows[:5]
        }

    @transaction.atomic
    def process_import(self):
        if not self.valid_rows:
            return 0, 0
            
        created_mappings = 0
        updated_schemes = 0
        
        # We need to process records.
        # Since AssessmentScheme is 1-to-1 with Subject, we upsert it.
        # CurriculumMapping is (Subject, Program, Semester), we get_or_create it.

        subject_ids = list(set(row['subject_id'] for row in self.valid_rows))
        
        existing_schemes = {
            scheme.subject_id: scheme 
            for scheme in AssessmentScheme.objects.filter(subject_id__in=subject_ids)
        }
        
        schemes_to_create = []
        schemes_to_update = []
        
        # Process unique subjects first for schemes
        processed_subjects = set()
        
        for data in self.valid_rows:
            subj_id = data['subject_id']
            
            # Map curriculum
            mapping, created = CurriculumMapping.objects.get_or_create(
                subject_id=subj_id,
                program_id=data['program_id'],
                semester=data['semester']
            )
            if created:
                created_mappings += 1

            # Assessment Scheme (process only once per subject per import file)
            if subj_id not in processed_subjects:
                if subj_id in existing_schemes:
                    # Update
                    scheme = existing_schemes[subj_id]
                    scheme.theory_ce = data['theory_ce']
                    scheme.theory_ese = data['theory_ese']
                    scheme.practical_ce = data['practical_ce']
                    scheme.practical_ese = data['practical_ese']
                    scheme.tutorial_ce = data['tutorial_ce']
                    scheme.tutorial_ese = data['tutorial_ese']
                    schemes_to_update.append(scheme)
                    updated_schemes += 1
                else:
                    # Create
                    schemes_to_create.append(AssessmentScheme(
                        subject_id=subj_id,
                        theory_ce=data['theory_ce'],
                        theory_ese=data['theory_ese'],
                        practical_ce=data['practical_ce'],
                        practical_ese=data['practical_ese'],
                        tutorial_ce=data['tutorial_ce'],
                        tutorial_ese=data['tutorial_ese']
                    ))
                    updated_schemes += 1 # Technically created scheme
                processed_subjects.add(subj_id)

        if schemes_to_create:
            AssessmentScheme.objects.bulk_create(schemes_to_create)
            
        if schemes_to_update:
            AssessmentScheme.objects.bulk_update(schemes_to_update, [
                'theory_ce', 'theory_ese', 'practical_ce', 'practical_ese',
                'tutorial_ce', 'tutorial_ese'
            ])

        return created_mappings, updated_schemes
