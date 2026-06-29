"""
Academic Structure Import Service.

Handles CSV and Excel (.xlsx) parsing, validation, and atomic import
of the complete academic structure (semesters, subjects, marks components).

Features:
- Supports both CSV and Excel formats
- Intelligent header detection (skips title rows)
- Dynamic marks component detection from column headers
- Semester carry-forward logic
- Auto-creates Subject records if not existing
- Auto-detects Program name from title row
- Subjects without codes use their name as the code
- Two-phase: validate() → process_import()
- Full transaction atomicity
"""
import csv
import io
import re
from django.db import transaction
from django.utils.text import slugify

from apps.master_data.models import Program, Subject
from apps.academic.models import (
    AcademicYear, Semester, SemesterSubject,
    MarksComponent, AcademicStructureImport,
)


class AcademicStructureImportService:
    """
    Parses an uploaded CSV/Excel file containing the teaching & examination scheme,
    validates it, and creates the full academic structure atomically.
    """

    # Required columns that must be present
    REQUIRED_COLUMNS = {'sem', 'course_code', 'course_title'}

    # Known marks column patterns (order matters for display_order)
    KNOWN_MARKS_COLUMNS = [
        'Theory CE', 'Theory ESE',
        'Practical CE', 'Practical ESE',
        'Tutorial CE', 'Tutorial ESE',
    ]

    def __init__(self, file_obj, filename, academic_year):
        """
        Args:
            file_obj: Uploaded file object (InMemoryUploadedFile or similar).
            filename: Original filename for format detection.
            academic_year: AcademicYear model instance.
        """
        self.file_obj = file_obj
        self.filename = filename
        self.academic_year = academic_year
        self.errors = []
        self.warnings = []
        self.valid_rows = []
        self.detected_marks_columns = []
        self.detected_program_name = ''
        self.file_format = 'xlsx' if filename.lower().endswith('.xlsx') else 'csv'

        # Caches
        self.subjects_cache = {s.code.upper(): s for s in Subject.objects.all()}

    def validate(self):
        """
        Phase 1: Parse and validate the file without writing to the database.
        Returns a summary dict with validation results.
        """
        self.errors = []
        self.warnings = []
        self.valid_rows = []

        try:
            if self.file_format == 'xlsx':
                self._parse_xlsx()
            else:
                self._parse_csv()
        except Exception as e:
            self.errors.append({
                'row': 0,
                'message': f"Failed to parse file: {str(e)}"
            })

        return self._get_summary()

    def _parse_xlsx(self):
        """Parse an Excel (.xlsx) file with intelligent header detection."""
        import openpyxl

        self.file_obj.seek(0)
        wb = openpyxl.load_workbook(self.file_obj, read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            self.errors.append({'row': 0, 'message': "File is empty."})
            return

        # Step 1: Detect program name from title rows
        self._detect_program_from_title_rows(rows)

        # Step 2: Find the header row (contains "Sem" or "Course Code")
        header_row_idx, column_map = self._find_headers_xlsx(rows)
        if header_row_idx is None:
            self.errors.append({
                'row': 0,
                'message': "Could not find header row. Expected columns: Sem, Course Code, Course Title."
            })
            return

        # Step 3: Parse data rows
        current_semester = None
        seen_codes = set()

        for row_idx in range(header_row_idx + 1, len(rows)):
            row = rows[row_idx]
            excel_row_num = row_idx + 1  # 1-indexed for error messages

            # Skip completely empty rows
            if not any(cell is not None and str(cell).strip() != '' for cell in row):
                continue

            # Extract values using column map
            sem_val = self._get_cell(row, column_map.get('sem'))
            code_val = self._get_cell(row, column_map.get('course_code'))
            title_val = self._get_cell(row, column_map.get('course_title'))

            # Handle semester carry-forward
            if sem_val is not None:
                try:
                    current_semester = int(float(str(sem_val)))
                except (ValueError, TypeError):
                    pass  # Not a semester row; ignore

            # Skip rows that have no course title (separator/summary rows)
            if not title_val:
                continue

            # If no course code, use the title as the code (per user request)
            if not code_val:
                code_val = self._generate_code_from_name(title_val)
                self.warnings.append({
                    'row': excel_row_num,
                    'message': f"No course code found. Using generated code: '{code_val}'"
                })

            if current_semester is None:
                self.errors.append({
                    'row': excel_row_num,
                    'course_code': code_val,
                    'message': "No semester number found before this row."
                })
                continue

            # Check for duplicate codes within this file
            code_upper = str(code_val).strip().upper()
            if code_upper in seen_codes:
                self.errors.append({
                    'row': excel_row_num,
                    'course_code': code_val,
                    'message': f"Duplicate subject code '{code_val}' in this file."
                })
                continue
            seen_codes.add(code_upper)

            # Parse marks columns
            marks = {}
            has_any_marks = False
            for col_name in self.detected_marks_columns:
                col_idx = column_map.get(col_name.lower().replace(' ', '_'))
                raw_val = self._get_cell(row, col_idx)
                parsed = self._safe_int(raw_val)

                if parsed is None:
                    self.errors.append({
                        'row': excel_row_num,
                        'course_code': code_val,
                        'message': f"Invalid marks value '{raw_val}' in column '{col_name}'."
                    })
                    marks = None
                    break

                marks[col_name] = parsed
                if parsed > 0:
                    has_any_marks = True

            if marks is None:
                continue

            # Skip rows where all marks are 0 (likely a section header)
            if not has_any_marks:
                self.warnings.append({
                    'row': excel_row_num,
                    'message': f"Subject '{code_val}' has all marks as 0. Skipping."
                })
                continue

            self.valid_rows.append({
                'row': excel_row_num,
                'semester': current_semester,
                'course_code': str(code_val).strip(),
                'course_title': str(title_val).strip(),
                'marks': marks,
            })

        wb.close()

    def _parse_csv(self):
        """Parse a CSV file."""
        self.file_obj.seek(0)
        try:
            decoded = self.file_obj.read().decode('utf-8', errors='replace')
        except AttributeError:
            decoded = self.file_obj.read()

        io_string = io.StringIO(decoded)
        reader = csv.reader(io_string)
        all_rows = list(reader)

        if not all_rows:
            self.errors.append({'row': 0, 'message': "File is empty."})
            return

        # Detect program from title
        self._detect_program_from_title_rows_csv(all_rows)

        # Find headers
        header_row_idx, column_map = self._find_headers_csv(all_rows)
        if header_row_idx is None:
            self.errors.append({
                'row': 0,
                'message': "Could not find header row. Expected: Sem, Course Code, Course Title."
            })
            return

        # Parse data rows
        current_semester = None
        seen_codes = set()

        for row_idx in range(header_row_idx + 1, len(all_rows)):
            row = all_rows[row_idx]
            excel_row_num = row_idx + 1

            if not any(cell.strip() for cell in row):
                continue

            sem_val = row[column_map.get('sem', -1)] if column_map.get('sem') is not None and column_map['sem'] < len(row) else ''
            code_val = row[column_map.get('course_code', -1)] if column_map.get('course_code') is not None and column_map['course_code'] < len(row) else ''
            title_val = row[column_map.get('course_title', -1)] if column_map.get('course_title') is not None and column_map['course_title'] < len(row) else ''

            sem_val = sem_val.strip() if sem_val else ''
            code_val = code_val.strip() if code_val else ''
            title_val = title_val.strip() if title_val else ''

            if sem_val:
                try:
                    current_semester = int(float(sem_val))
                except (ValueError, TypeError):
                    pass

            if not title_val:
                continue

            if not code_val:
                code_val = self._generate_code_from_name(title_val)
                self.warnings.append({
                    'row': excel_row_num,
                    'message': f"No course code. Using: '{code_val}'"
                })

            if current_semester is None:
                self.errors.append({
                    'row': excel_row_num,
                    'course_code': code_val,
                    'message': "No semester number found before this row."
                })
                continue

            code_upper = code_val.upper()
            if code_upper in seen_codes:
                self.errors.append({
                    'row': excel_row_num,
                    'course_code': code_val,
                    'message': f"Duplicate code '{code_val}'."
                })
                continue
            seen_codes.add(code_upper)

            marks = {}
            has_any_marks = False
            for col_name in self.detected_marks_columns:
                col_idx = column_map.get(col_name.lower().replace(' ', '_'))
                if col_idx is not None and col_idx < len(row):
                    raw_val = row[col_idx].strip()
                else:
                    raw_val = ''

                parsed = self._safe_int(raw_val)
                if parsed is None:
                    self.errors.append({
                        'row': excel_row_num,
                        'course_code': code_val,
                        'message': f"Invalid marks '{raw_val}' for '{col_name}'."
                    })
                    marks = None
                    break

                marks[col_name] = parsed
                if parsed > 0:
                    has_any_marks = True

            if marks is None:
                continue

            if not has_any_marks:
                continue

            self.valid_rows.append({
                'row': excel_row_num,
                'semester': current_semester,
                'course_code': code_val,
                'course_title': title_val,
                'marks': marks,
            })

    def _detect_program_from_title_rows(self, rows):
        """
        Scan the first 5 rows for a title containing program info.
        Pattern: "TEACHING & EXAMINATION SCHEME FOR <PROGRAM NAME> AY: YYYY-YY"
        """
        for row in rows[:10]:
            for cell in row:
                if cell and isinstance(cell, str):
                    text = cell.strip()
                    # Try to extract program name
                    match = re.search(
                        r'(?:SCHEME\s+FOR|FOR)\s+(.+?)(?:\s+AY\s*[:.]|\s+ACADEMIC\s+YEAR|\s*$)',
                        text,
                        re.IGNORECASE
                    )
                    if match:
                        self.detected_program_name = match.group(1).strip()
                        return
                    # Also try: "DIPLOMA IN ..." pattern
                    match2 = re.search(
                        r'((?:DIPLOMA|DEGREE|B\.?\s*TECH|M\.?\s*TECH|B\.?\s*E|M\.?\s*E)\s+(?:IN\s+)?.+?)(?:\s+AY|\s+BATCH|\s*$)',
                        text,
                        re.IGNORECASE
                    )
                    if match2:
                        self.detected_program_name = match2.group(1).strip()
                        return

    def _detect_program_from_title_rows_csv(self, rows):
        """CSV version of title detection."""
        for row in rows[:10]:
            for cell in row:
                if cell and cell.strip():
                    text = cell.strip()
                    match = re.search(
                        r'(?:SCHEME\s+FOR|FOR)\s+(.+?)(?:\s+AY\s*[:.]|\s+ACADEMIC|\s*$)',
                        text,
                        re.IGNORECASE
                    )
                    if match:
                        self.detected_program_name = match.group(1).strip()
                        return

    def _find_headers_xlsx(self, rows):
        """
        Find the header row in Excel data.
        The Excel file has a multi-row header structure:
            Row N: Sem | Course Code | Course Title | Examination Scheme ...
            Row N+1: (empty) | (empty) | (empty) | Theory | Practical | Tutorial | Total
            Row N+2: (empty) | (empty) | (empty) | CE | ESE | CE | ESE | CE | ESE

        We need to combine these to build the full column map.
        """
        column_map = {}

        for idx, row in enumerate(rows):
            row_strs = [str(cell).strip().lower() if cell else '' for cell in row]

            # Look for the main header row containing 'sem' or 'course code'
            if any(val in ('sem', 'semester') for val in row_strs):
                # Found the main header row
                for col_idx, val in enumerate(row_strs):
                    if val in ('sem', 'semester'):
                        column_map['sem'] = col_idx
                    elif val in ('course code', 'subject code', 'code'):
                        column_map['course_code'] = col_idx
                    elif val in ('course title', 'subject name', 'course name', 'subject title', 'title'):
                        column_map['course_title'] = col_idx

                # Now look at the sub-header rows to find marks columns
                # Check next 1-3 rows for category headers and CE/ESE labels
                category_row = None
                detail_row = None

                if idx + 1 < len(rows):
                    next_row = [str(c).strip() if c else '' for c in rows[idx + 1]]
                    # Check if this row has category headers (Theory, Practical, Tutorial)
                    if any(v.lower() in ('theory', 'practical', 'tutorial') for v in next_row):
                        category_row = next_row

                if idx + 2 < len(rows):
                    next_next_row = [str(c).strip() if c else '' for c in rows[idx + 2]]
                    # Check if this row has CE/ESE labels
                    if any(v.lower() in ('ce', 'ese') for v in next_next_row):
                        detail_row = next_next_row

                if category_row and detail_row:
                    # Multi-row header: combine category + detail
                    self._build_marks_columns_multi(column_map, category_row, detail_row)
                    return idx + 2, column_map  # Data starts after detail row
                elif category_row:
                    # Just category row — use as marks columns
                    self._build_marks_columns_single(column_map, category_row)
                    return idx + 1, column_map
                else:
                    # All in one row — unlikely but handle it
                    self._build_marks_columns_from_header(column_map, row_strs)
                    return idx, column_map

        return None, {}

    def _build_marks_columns_multi(self, column_map, category_row, detail_row):
        """
        Build marks columns from a multi-row header structure.
        category_row: [..., 'Theory', '', 'Practical', '', 'Tutorial', '', 'Total']
        detail_row:   [..., 'CE', 'ESE', 'CE', 'ESE', 'CE', 'ESE', '']
        """
        current_category = None

        for col_idx in range(len(detail_row)):
            # Track the current category from the category row
            cat_val = category_row[col_idx].strip() if col_idx < len(category_row) else ''
            if cat_val and cat_val.lower() not in ('', 'total', 'examination scheme'):
                current_category = cat_val

            detail_val = detail_row[col_idx].strip() if detail_row[col_idx] else ''

            if detail_val and current_category and detail_val.lower() not in ('total',):
                # Combine: "Theory" + "CE" → "Theory CE"
                full_name = f"{current_category} {detail_val}"
                slug_key = full_name.lower().replace(' ', '_')
                column_map[slug_key] = col_idx
                if full_name not in self.detected_marks_columns:
                    self.detected_marks_columns.append(full_name)

    def _build_marks_columns_single(self, column_map, header_row):
        """Build marks columns from a single header row."""
        for col_idx, val in enumerate(header_row):
            val_clean = val.strip()
            if val_clean and val_clean.lower() not in ('', 'sem', 'semester', 'course code',
                                                        'course title', 'total', 'subject code',
                                                        'subject name', 'code', 'title',
                                                        'examination scheme', 'course name',
                                                        'subject title'):
                slug_key = val_clean.lower().replace(' ', '_')
                column_map[slug_key] = col_idx
                if val_clean not in self.detected_marks_columns:
                    self.detected_marks_columns.append(val_clean)

    def _build_marks_columns_from_header(self, column_map, header_row):
        """Fallback: marks columns from the same header row."""
        self._build_marks_columns_single(column_map, header_row)

    def _find_headers_csv(self, rows):
        """Find header row in CSV data."""
        column_map = {}

        for idx, row in enumerate(rows):
            row_lower = [cell.strip().lower() for cell in row]

            if any(val in ('sem', 'semester') for val in row_lower):
                for col_idx, val in enumerate(row_lower):
                    if val in ('sem', 'semester'):
                        column_map['sem'] = col_idx
                    elif val in ('course code', 'subject code', 'code'):
                        column_map['course_code'] = col_idx
                    elif val in ('course title', 'subject name', 'course name', 'subject title', 'title'):
                        column_map['course_title'] = col_idx

                # Check for marks columns in the same row or subsequent rows
                remaining_cols = [cell.strip() for cell in row]
                for col_idx, val in enumerate(remaining_cols):
                    if val.lower() not in ('', 'sem', 'semester', 'course code', 'subject code',
                                           'course title', 'subject name', 'total', 'code',
                                           'title', 'course name', 'subject title'):
                        slug_key = val.lower().replace(' ', '_')
                        column_map[slug_key] = col_idx
                        if val not in self.detected_marks_columns:
                            self.detected_marks_columns.append(val)

                return idx, column_map

        return None, {}

    def _get_cell(self, row, col_idx):
        """Safely get a cell value from a row."""
        if col_idx is None or col_idx >= len(row):
            return None
        val = row[col_idx]
        if val is None:
            return None
        # Handle formula strings (from openpyxl data_only=True mode)
        val_str = str(val).strip()
        if val_str.startswith('='):
            return None  # Skip formula cells
        if val_str == '':
            return None
        return val_str

    def _safe_int(self, value):
        """Convert a value to int, returning 0 for empty/blank, None for invalid."""
        if value is None or str(value).strip() == '':
            return 0
        try:
            result = int(float(str(value).strip()))
            if result < 0:
                return None
            return result
        except (ValueError, TypeError):
            return None

    def _generate_code_from_name(self, name):
        """
        Generate a subject code from the name when no code is provided.
        e.g., "Language Training Elective Course" → "LTEC"
        """
        words = re.findall(r'[A-Za-z]+', name)
        if not words:
            return slugify(name).upper()[:20]

        # Take first letter of each word, uppercase
        code = ''.join(w[0].upper() for w in words)

        # Ensure uniqueness by appending digits if needed
        if len(code) < 3:
            code = slugify(name).replace('-', '').upper()[:10]

        return code

    def _get_summary(self):
        """Build a summary dict of the validation results."""
        # Count unique semesters
        semesters = set(r['semester'] for r in self.valid_rows)

        return {
            'total_valid': len(self.valid_rows),
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'unique_semesters': sorted(semesters),
            'total_semesters': len(semesters),
            'detected_marks_columns': self.detected_marks_columns,
            'detected_program': self.detected_program_name,
            'errors': self.errors[:100],
            'warnings': self.warnings[:50],
            'valid_sample': self.valid_rows[:10],
            'file_format': self.file_format,
        }

    @transaction.atomic
    def process_import(self, imported_by=None):
        """
        Phase 2: Commit validated data to the database.
        Must call validate() first.

        Returns:
            AcademicStructureImport instance with results.
        """
        if not self.valid_rows:
            import_record = AcademicStructureImport.objects.create(
                academic_year=self.academic_year,
                original_filename=self.filename,
                file_format=self.file_format,
                imported_by=imported_by,
                status=AcademicStructureImport.ImportStatus.FAILED,
                summary={'error': 'No valid rows to import.'},
                error_log=self.errors,
                program_name=self.detected_program_name,
            )
            return import_record

        # Auto-create/get Program if detected
        program = None
        if self.detected_program_name:
            program_code = self._generate_code_from_name(self.detected_program_name)
            program, _ = Program.objects.get_or_create(
                code=program_code.upper(),
                defaults={'name': self.detected_program_name}
            )

        # Track counts
        semesters_created = 0
        subjects_created = 0
        components_created = 0

        # Group rows by semester
        semester_groups = {}
        for row_data in self.valid_rows:
            sem_num = row_data['semester']
            if sem_num not in semester_groups:
                semester_groups[sem_num] = []
            semester_groups[sem_num].append(row_data)

        # Create semesters
        for sem_num in sorted(semester_groups.keys()):
            semester, created = Semester.objects.get_or_create(
                academic_year=self.academic_year,
                number=sem_num,
                defaults={'name': f"Semester {sem_num}"}
            )
            if created:
                semesters_created += 1

            # Create subjects within this semester
            for row_data in semester_groups[sem_num]:
                code = row_data['course_code'].strip().upper()
                title = row_data['course_title'].strip()

                # Get or create the global Subject
                subject = self.subjects_cache.get(code)
                if not subject:
                    subject, _ = Subject.objects.get_or_create(
                        code=code,
                        defaults={'name': title}
                    )
                    self.subjects_cache[code] = subject
                    subjects_created += 1

                # Create SemesterSubject
                sem_subject, _ = SemesterSubject.objects.get_or_create(
                    semester=semester,
                    subject=subject,
                    defaults={
                        'subject_code': subject.code,
                        'subject_name': title,
                    }
                )

                # Create MarksComponents
                for order, (comp_name, max_marks) in enumerate(row_data['marks'].items()):
                    if max_marks > 0:
                        comp_slug = slugify(comp_name).replace('-', '_')
                        MarksComponent.objects.get_or_create(
                            semester_subject=sem_subject,
                            slug=comp_slug,
                            defaults={
                                'name': comp_name,
                                'max_marks': max_marks,
                                'display_order': order,
                            }
                        )
                        components_created += 1

                # Also create CurriculumMapping for backward compat if program exists
                if program:
                    from apps.curriculum.models import CurriculumMapping, AssessmentScheme
                    CurriculumMapping.objects.get_or_create(
                        subject=subject,
                        program=program,
                        semester=sem_num,
                    )

                    # Also create/update legacy AssessmentScheme
                    marks = row_data['marks']
                    scheme_data = {
                        'theory_ce': marks.get('Theory CE', 0),
                        'theory_ese': marks.get('Theory ESE', 0),
                        'practical_ce': marks.get('Practical CE', 0),
                        'practical_ese': marks.get('Practical ESE', 0),
                        'tutorial_ce': marks.get('Tutorial CE', 0),
                        'tutorial_ese': marks.get('Tutorial ESE', 0),
                    }
                    AssessmentScheme.objects.update_or_create(
                        subject=subject,
                        defaults=scheme_data,
                    )

        # Create import record
        import_record = AcademicStructureImport.objects.create(
            academic_year=self.academic_year,
            original_filename=self.filename,
            file_format=self.file_format,
            imported_by=imported_by,
            status=AcademicStructureImport.ImportStatus.SUCCESS,
            summary={
                'semesters_created': semesters_created,
                'subjects_created': subjects_created,
                'components_created': components_created,
                'total_rows_processed': len(self.valid_rows),
                'detected_marks_columns': self.detected_marks_columns,
            },
            error_log=self.errors,
            program_name=self.detected_program_name,
        )

        return import_record
