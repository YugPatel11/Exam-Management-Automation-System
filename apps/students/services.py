import csv
import io
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.students.models import Student

class StudentImportService:
    """
    Handles CSV parsing, validation, and importing of Student data based on academic structure.
    Expected columns: student_name, enrollment_number, division, batch
    """
    
    EXPECTED_COLUMNS = [
        'student_name', 'enrollment_number', 'division', 'batch'
    ]

    def __init__(self, file_obj, academic_year_id=None):
        self.file_obj = file_obj
        self.academic_year_id = academic_year_id
        self.errors = []
        self.valid_rows = []

    def validate_file(self):
        """
        Parses the CSV and categorizes rows into valid_rows or errors.
        Returns a dict with summary statistics.
        """
        if not self.academic_year_id:
            self.errors.append({
                'row': 0,
                'message': "Academic Year must be provided."
            })
            return self._get_summary()

        try:
            # Decode file assuming utf-8. We use 'replace' to avoid hard crashes on weird characters.
            decoded_file = self.file_obj.read().decode('utf-8', errors='replace')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Check headers
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

    def _validate_row(self, row_idx, row):
        """
        Validates a single row and appends to valid_rows or errors.
        """
        # Clean data
        data = {k: str(v).strip() if v else '' for k, v in row.items()}
        
        name = data.get('student_name')
        enrollment_no = data.get('enrollment_number')
        division = data.get('division', '')
        batch = data.get('batch', '')
        
        # Basic Required checks
        if not all([name, enrollment_no, division]):
            self.errors.append({
                'row': row_idx,
                'enrollment_no': enrollment_no or 'Unknown',
                'message': "Missing one or more required fields (student_name, enrollment_number, division)."
            })
            return

        # Passed all checks
        self.valid_rows.append({
            'row': row_idx,
            'enrollment_no': enrollment_no,
            'name': name,
            'class_name': division.upper(),
            'batch': batch.upper(),
        })

    def _get_summary(self):
        return {
            'total_valid': len(self.valid_rows),
            'total_errors': len(self.errors),
            'errors': self.errors[:100],  # Return max 100 errors to prevent huge payloads
            'valid_sample': self.valid_rows[:5]  # Sample for preview
        }

    @transaction.atomic
    def process_import(self):
        """
        Commits valid_rows to the database for the given Academic Year.
        Updates existing records by EnrollmentNo + AcademicYear or creates new ones.
        """
        if not self.valid_rows or not self.academic_year_id:
            return 0, 0
            
        created_count = 0
        updated_count = 0
        
        # Fetch existing students to handle updates efficiently
        enrollment_nos = [row['enrollment_no'] for row in self.valid_rows]
        existing_students = {
            s.enrollment_no: s for s in Student.objects.filter(
                academic_year_id=self.academic_year_id,
                enrollment_no__in=enrollment_nos
            )
        }
        
        students_to_create = []
        students_to_update = []
        
        for data in self.valid_rows:
            enrollment_no = data['enrollment_no']
            
            if enrollment_no in existing_students:
                # Update existing
                student = existing_students[enrollment_no]
                student.name = data['name']
                student.class_name = data['class_name']
                student.batch = data['batch']
                student.roll_no = data['enrollment_no']
                students_to_update.append(student)
                updated_count += 1
            else:
                # Create new
                student = Student(
                    academic_year_id=self.academic_year_id,
                    enrollment_no=data['enrollment_no'],
                    roll_no=data['enrollment_no'],
                    name=data['name'],
                    class_name=data['class_name'],
                    batch=data['batch']
                )
                students_to_create.append(student)
                created_count += 1
                
        # Bulk operations
        if students_to_create:
            Student.objects.bulk_create(students_to_create, batch_size=500)
            
        if students_to_update:
            update_fields = ['name', 'class_name', 'batch', 'roll_no']
            Student.objects.bulk_update(students_to_update, update_fields, batch_size=500)
            
        return created_count, updated_count
