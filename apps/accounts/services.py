import csv
import io
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model


class UserCsvImportService:
    def __init__(self, creator):
        self.creator = creator
        self.errors = []
        self.success_count = 0
        
    def process(self, csv_file):
        """
        Processes an uploaded CSV file to create users.
        Expected columns: FirstName, LastName, Email, Role, Phone, Department, Designation, EmployeeId
        """
        User = get_user_model()
        
        try:
            # Read CSV
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Validate headers
            headers = reader.fieldnames
            required_headers = ['FirstName', 'LastName', 'Email', 'Role']
            
            for header in required_headers:
                if header not in headers:
                    self.errors.append(f"CSV must contain a '{header}' column.")
                    
            if self.errors:
                return False
                
            allowed_roles = ['subject_coordinator', 'subject_faculty']
            if self.creator.is_admin_role or self.creator.is_superuser:
                allowed_roles.extend(['admin', 'exam_coordinator'])
                
            users_to_create = []
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    # Skip completely empty rows
                    if not any(str(v).strip() for v in row.values() if v is not None):
                        continue

                    email = str(row.get('Email') or '').strip()
                    if not email:
                        self.errors.append(f"Row {row_num}: Email is required.")
                        continue
                        
                    if User.objects.filter(email=email).exists():
                        self.errors.append(f"Row {row_num}: User with email {email} already exists.")
                        continue
                        
                    role = str(row.get('Role') or '').strip()
                    if role not in allowed_roles:
                        self.errors.append(f"Row {row_num}: Invalid or unauthorized role '{role}'. Allowed: {', '.join(allowed_roles)}.")
                        continue
                        
                    first_name = str(row.get('FirstName') or '').strip()
                    last_name = str(row.get('LastName') or '').strip()
                    phone = str(row.get('Phone') or '').strip()
                    department = str(row.get('Department') or '').strip()
                    designation = str(row.get('Designation') or '').strip()
                    employee_id = str(row.get('EmployeeId') or '').strip() or None
                    
                    if employee_id and User.objects.filter(employee_id=employee_id).exists():
                        self.errors.append(f"Row {row_num}: Employee ID {employee_id} already exists.")
                        continue
                        
                    # Auto-generate password
                    raw_password = get_random_string(length=12)
                    
                    user = User(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=role,
                        phone=phone,
                        department=department,
                        designation=designation,
                        employee_id=employee_id
                    )
                    user.set_password(raw_password)
                    users_to_create.append((user, raw_password))
                    
                if not self.errors:
                    # Create users and send emails
                    for user, pwd in users_to_create:
                        user.save()
                        self.success_count += 1
                        
                        # Send welcome email
                        subject = 'Welcome to EMS - Your Account Details'
                        message = f"Hello {user.get_display_name()},\n\nYour account has been created via CSV import.\nLogin Email: {user.email}\nPassword: {pwd}\n\nPlease log in and change your password immediately."
                        try:
                            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
                        except Exception:
                            pass # We continue even if email fails
                            
            return len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"Error processing CSV: {str(e)}")
            return False
