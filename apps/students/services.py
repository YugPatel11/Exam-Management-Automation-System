import csv
import io
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.master_data.models import Program, Division
from apps.students.models import Student

class StudentImportService:
    """
    Handles CSV parsing, validation, and importing of Student data.
    """
    
    EXPECTED_COLUMNS = [
        'RollNo', 'EnrollmentNo', 'StudentName', 'ProgramName',
        'Semester', 'DivisionCode', 'LabBatchNo', 'Gender',
        'StudentDisplayNo', 'AdmissionApplicationNo', 'PhoneStudent1',
        'PhoneStudent2', 'Email'
    ]

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.errors = []
        self.valid_rows = []
        
        # Cache master data to avoid N+1 DB queries during validation
        self.programs_cache = {p.code.upper(): p for p in Program.objects.filter(is_archived=False)}
        
        # Cache divisions keyed by (program_id, semester, name_upper)
        self.divisions_cache = {}
        for d in Division.objects.filter(is_archived=False).select_related('program'):
            key = (d.program_id, d.semester, d.name.upper())
            self.divisions_cache[key] = d

    def validate_file(self):
        """
        Parses the CSV and categorizes rows into valid_rows or errors.
        Returns a dict with summary statistics.
        """
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
        
        roll_no = data.get('RollNo')
        enrollment_no = data.get('EnrollmentNo')
        name = data.get('StudentName')
        program_code = data.get('ProgramName')
        semester_str = data.get('Semester')
        division_code = data.get('DivisionCode')
        
        # Basic Required checks
        if not all([roll_no, enrollment_no, name, program_code, semester_str]):
            self.errors.append({
                'row': row_idx,
                'roll_no': roll_no or 'Unknown',
                'message': "Missing one or more required fields (RollNo, EnrollmentNo, Name, ProgramName, Semester)."
            })
            return

        # Semester Integer Check
        try:
            semester = int(semester_str)
        except ValueError:
            self.errors.append({
                'row': row_idx,
                'roll_no': roll_no,
                'message': f"Invalid Semester '{semester_str}'. Must be an integer."
            })
            return

        # Program Check / Auto-Create
        program = self.programs_cache.get(program_code.upper())
        if not program:
            # Auto-create missing program
            program, _ = Program.objects.get_or_create(
                code=program_code.upper(),
                defaults={'name': program_code} # Fallback name
            )
            self.programs_cache[program_code.upper()] = program
            
        # Division Check / Auto-Create
        division = None
        if division_code:
            div_key = (program.id, semester, division_code.upper())
            division = self.divisions_cache.get(div_key)
            if not division:
                # Auto-create missing division
                division, _ = Division.objects.get_or_create(
                    program=program,
                    semester=semester,
                    name=division_code.upper()
                )
                self.divisions_cache[div_key] = division

        # Gender Mapping
        raw_gender = data.get('Gender', '').upper()
        if raw_gender.startswith('M'):
            gender = 'M'
        elif raw_gender.startswith('F'):
            gender = 'F'
        else:
            gender = 'O'

        # Passed all checks
        self.valid_rows.append({
            'row': row_idx,
            'roll_no': roll_no,
            'enrollment_no': enrollment_no,
            'name': name,
            'program_id': program.id,
            'semester': semester,
            'division_id': division.id if division else None,
            'lab_batch_no': data.get('LabBatchNo', ''),
            'gender': gender,
            'display_no': data.get('StudentDisplayNo', ''),
            'admission_application_no': data.get('AdmissionApplicationNo', ''),
            'phone_1': data.get('PhoneStudent1', ''),
            'phone_2': data.get('PhoneStudent2', ''),
            'email': data.get('Email', '')
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
        Commits valid_rows to the database.
        Updates existing records by RollNo/EnrollmentNo or creates new ones.
        """
        if not self.valid_rows:
            return 0, 0
            
        created_count = 0
        updated_count = 0
        
        # Fetch existing students to handle updates efficiently
        roll_nos = [row['roll_no'] for row in self.valid_rows]
        existing_students = {
            s.roll_no: s for s in Student.objects.filter(roll_no__in=roll_nos)
        }
        
        students_to_create = []
        students_to_update = []
        
        for data in self.valid_rows:
            roll_no = data['roll_no']
            
            if roll_no in existing_students:
                # Update existing
                student = existing_students[roll_no]
                student.enrollment_no = data['enrollment_no']
                student.name = data['name']
                student.program_id = data['program_id']
                student.semester = data['semester']
                student.division_id = data['division_id']
                student.lab_batch_no = data['lab_batch_no']
                student.gender = data['gender']
                student.display_no = data['display_no']
                student.admission_application_no = data['admission_application_no']
                student.phone_1 = data['phone_1']
                student.phone_2 = data['phone_2']
                student.email = data['email']
                students_to_update.append(student)
                updated_count += 1
            else:
                # Create new
                student = Student(
                    roll_no=data['roll_no'],
                    enrollment_no=data['enrollment_no'],
                    name=data['name'],
                    program_id=data['program_id'],
                    semester=data['semester'],
                    division_id=data['division_id'],
                    lab_batch_no=data['lab_batch_no'],
                    gender=data['gender'],
                    display_no=data['display_no'],
                    admission_application_no=data['admission_application_no'],
                    phone_1=data['phone_1'],
                    phone_2=data['phone_2'],
                    email=data['email']
                )
                students_to_create.append(student)
                created_count += 1
                
        # Bulk operations
        if students_to_create:
            Student.objects.bulk_create(students_to_create, batch_size=500)
            
        if students_to_update:
            update_fields = [
                'enrollment_no', 'name', 'program_id', 'semester', 'division_id',
                'lab_batch_no', 'gender', 'display_no', 'admission_application_no',
                'phone_1', 'phone_2', 'email'
            ]
            Student.objects.bulk_update(students_to_update, update_fields, batch_size=500)
            
        return created_count, updated_count
