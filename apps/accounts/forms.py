"""
Authentication and user management forms with Tailwind CSS styling.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import get_user_model

User = get_user_model()

# Shared Tailwind CSS classes for form inputs
INPUT_CLASSES = (
    'w-full px-4 py-3 rounded-lg border border-slate-300 bg-white '
    'text-slate-900 placeholder-slate-400 '
    'focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 '
    'dark:bg-slate-800 dark:border-slate-600 dark:text-slate-100 '
    'dark:placeholder-slate-500 dark:focus:ring-teal-400 '
    'transition duration-200'
)

SELECT_CLASSES = (
    'w-full px-4 py-3 rounded-lg border border-slate-300 bg-white '
    'text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 '
    'focus:border-teal-500 dark:bg-slate-800 dark:border-slate-600 '
    'dark:text-slate-100 transition duration-200'
)


class LoginForm(AuthenticationForm):
    """Custom login form with styled fields."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Enter your email or username',
            'autocomplete': 'username',
            'id': 'login-username',
        }),
        label='Email or Username',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'id': 'login-password',
        }),
        label='Password',
    )


class ChangePasswordForm(PasswordChangeForm):
    """Custom password change form with styled fields."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Current password',
            'id': 'change-old-password',
        }),
        label='Current Password',
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'New password',
            'id': 'change-new-password',
        }),
        label='New Password',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Confirm new password',
            'id': 'change-confirm-password',
        }),
        label='Confirm New Password',
    )


class ForgotPasswordForm(forms.Form):
    """Form for initiating password reset via email."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Enter your registered email',
            'id': 'forgot-email',
        }),
        label='Email Address',
    )


class ResetPasswordForm(SetPasswordForm):
    """Form for setting a new password during reset."""
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'New password',
            'id': 'reset-new-password',
        }),
        label='New Password',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Confirm new password',
            'id': 'reset-confirm-password',
        }),
        label='Confirm New Password',
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'designation']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'First name', 'id': 'profile-first-name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Last name', 'id': 'profile-last-name'
            }),
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Email address', 'id': 'profile-email'
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Phone number', 'id': 'profile-phone'
            }),
            'department': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Department', 'id': 'profile-department'
            }),
            'designation': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Designation', 'id': 'profile-designation'
            }),
        }


class UserCreateForm(forms.ModelForm):
    """Form for admin to create new user accounts."""
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Password',
            'id': 'create-password',
        }),
        label='Password',
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Confirm password',
            'id': 'create-confirm-password',
        }),
        label='Confirm Password',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role',
                  'phone', 'department', 'designation', 'employee_id']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Username', 'id': 'create-username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'First name', 'id': 'create-first-name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Last name', 'id': 'create-last-name'
            }),
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Email', 'id': 'create-email'
            }),
            'role': forms.Select(attrs={
                'class': SELECT_CLASSES, 'id': 'create-role'
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Phone', 'id': 'create-phone'
            }),
            'department': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Department', 'id': 'create-department'
            }),
            'designation': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Designation', 'id': 'create-designation'
            }),
            'employee_id': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'Employee ID', 'id': 'create-employee-id'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class AdminUserCreateForm(forms.ModelForm):
    """Form for Admins/Exam Coordinators to create users.
    Admin can create all roles including exam_coordinator.
    Exam Coordinator can only create subject_coordinator and subject_faculty.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'phone', 'department', 'designation', 'employee_id']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'First name', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Last name', 'required': True}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Email (used for login)', 'required': True}),
            'role': forms.Select(attrs={'class': SELECT_CLASSES}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Phone'}),
            'department': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Department'}),
            'designation': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Designation'}),
            'employee_id': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Employee ID'}),
        }

    def __init__(self, *args, **kwargs):
        self.creator = kwargs.pop('creator', None)
        super().__init__(*args, **kwargs)
        if self.creator:
            if self.creator.role == 'admin' or self.creator.is_superuser:
                # Admin can create all roles except admin
                self.fields['role'].choices = [
                    ('exam_coordinator', 'Exam Coordinator'),
                    ('subject_coordinator', 'Subject Coordinator'),
                    ('subject_faculty', 'Subject Faculty'),
                ]
            else:
                # Exam Coordinator can only create faculty roles
                self.fields['role'].choices = [
                    ('subject_coordinator', 'Subject Coordinator'),
                    ('subject_faculty', 'Subject Faculty'),
                ]

