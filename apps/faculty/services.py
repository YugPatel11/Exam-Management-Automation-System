import csv
import io
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.master_data.models import Subject
from apps.faculty.models import SubjectCoordinatorAssignment, SubjectFacultyAssignment

User = get_user_model()

class CoordinatorImportService:
    """
    Handles CSV parsing, validation, and importing of Subject Coordinator Assignments.
    """
    EXPECTED_COLUMNS = ['subject code', 'subject name', 'subject coordinator']

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.errors = []
        self.valid_rows = []
        
        # Caches
        self.subjects_cache = {s.code.upper(): s for s in Subject.objects.all()}
        # Match users by email
        self.users_cache = {u.email.lower(): u for u in User.objects.exclude(email='')}

    def validate_file(self):
        try:
            decoded_file = self.file_obj.read().decode('utf-8', errors='replace')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Normalize headers to lowercase for flexible matching
            headers = [h.strip().lower() for h in reader.fieldnames] if reader.fieldnames else []
            missing_cols = [col for col in self.EXPECTED_COLUMNS if col not in headers]
            if missing_cols:
                self.errors.append({
                    'row': 0,
                    'message': f"Missing required columns: {', '.join(missing_cols)}"
                })
                return self._get_summary()

            # Map the actual headers back if they had weird casing
            header_map = {h.strip().lower(): h for h in reader.fieldnames}

            for row_idx, row in enumerate(reader, start=1):
                self._validate_row(row_idx, row, header_map)
                
        except Exception as e:
            self.errors.append({
                'row': 0,
                'message': f"Failed to parse CSV: {str(e)}"
            })
            
        return self._get_summary()

    def _validate_row(self, row_idx, row, header_map):
        course_code = str(row.get(header_map['subject code'], '')).strip()
        course_title = str(row.get(header_map['subject name'], '')).strip()
        coordinator_email = str(row.get(header_map['subject coordinator'], '')).strip().lower()

        if not all([course_code, course_title, coordinator_email]):
            self.errors.append({
                'row': row_idx,
                'identifier': course_code or 'Unknown',
                'message': "Missing one or more required fields (Subject Code, Subject Name, Subject Coordinator)."
            })
            return

        # Subject Check / Auto-Create
        subject = self.subjects_cache.get(course_code.upper())
        if not subject:
            subject, _ = Subject.objects.get_or_create(
                code=course_code.upper(),
                defaults={'name': course_title}
            )
            self.subjects_cache[course_code.upper()] = subject

        # User Check
        user = self.users_cache.get(coordinator_email)
        if not user:
            self.errors.append({
                'row': row_idx,
                'identifier': course_code,
                'message': f"User with email '{coordinator_email}' not found. Cannot assign coordinator."
            })
            return

        self.valid_rows.append({
            'row': row_idx,
            'subject_id': subject.id,
            'course_code': subject.code,
            'course_title': subject.name,
            'user_id': user.id,
            'user_email': user.email,
            'user_name': user.get_display_name()
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
            return 0
            
        created_count = 0
        
        for data in self.valid_rows:
            assignment, created = SubjectCoordinatorAssignment.objects.get_or_create(
                subject_id=data['subject_id'],
                coordinator_id=data['user_id']
            )
            if created:
                created_count += 1
                
            # Optionally upgrade user's base role if it's lesser than coordinator
            # But the spec says roles can be both, assignment dictates permission.
            
        return created_count


class FacultyImportService:
    """
    Handles CSV parsing, validation, and importing of Subject Faculty Assignments.
    """
    EXPECTED_COLUMNS = ['subject code', 'subject name', 'division', 'faculty']

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.errors = []
        self.valid_rows = []
        
        self.subjects_cache = {s.code.upper(): s for s in Subject.objects.all()}
        self.users_cache = {u.email.lower(): u for u in User.objects.exclude(email='')}

    def validate_file(self):
        try:
            decoded_file = self.file_obj.read().decode('utf-8', errors='replace')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            headers = [h.strip().lower() for h in reader.fieldnames] if reader.fieldnames else []
            missing_cols = [col for col in self.EXPECTED_COLUMNS if col not in headers]
            if missing_cols:
                self.errors.append({
                    'row': 0,
                    'message': f"Missing required columns: {', '.join(missing_cols)}"
                })
                return self._get_summary()

            header_map = {h.strip().lower(): h for h in reader.fieldnames}

            for row_idx, row in enumerate(reader, start=1):
                self._validate_row(row_idx, row, header_map)
                
        except Exception as e:
            self.errors.append({
                'row': 0,
                'message': f"Failed to parse CSV: {str(e)}"
            })
            
        return self._get_summary()

    def _validate_row(self, row_idx, row, header_map):
        course_code = str(row.get(header_map['subject code'], '')).strip()
        course_title = str(row.get(header_map['subject name'], '')).strip()
        division_name = str(row.get(header_map['division'], '')).strip()
        faculty_email = str(row.get(header_map['faculty'], '')).strip().lower()

        if not all([course_code, course_title, division_name, faculty_email]):
            self.errors.append({
                'row': row_idx,
                'identifier': course_code or 'Unknown',
                'message': "Missing one or more required fields (Subject Code, Name, Division, Faculty)."
            })
            return

        subject = self.subjects_cache.get(course_code.upper())
        if not subject:
            subject, _ = Subject.objects.get_or_create(
                code=course_code.upper(),
                defaults={'name': course_title}
            )
            self.subjects_cache[course_code.upper()] = subject

        user = self.users_cache.get(faculty_email)
        if not user:
            self.errors.append({
                'row': row_idx,
                'identifier': course_code,
                'message': f"User with email '{faculty_email}' not found. Cannot assign faculty."
            })
            return

        self.valid_rows.append({
            'row': row_idx,
            'subject_id': subject.id,
            'course_code': subject.code,
            'course_title': subject.name,
            'division_name': division_name.upper(),
            'user_id': user.id,
            'user_email': user.email,
            'user_name': user.get_display_name()
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
            return 0
            
        created_count = 0
        
        for data in self.valid_rows:
            assignment, created = SubjectFacultyAssignment.objects.get_or_create(
                subject_id=data['subject_id'],
                faculty_id=data['user_id'],
                division_name=data['division_name']
            )
            if created:
                created_count += 1
                
        return created_count
