"""
Authentication views for the EMS system.
Handles login, logout, password management, and profile.
"""
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import (
    LoginForm, ChangePasswordForm, ForgotPasswordForm,
    ResetPasswordForm, UserProfileForm, AdminUserCreateForm
)
from apps.accounts.models import PasswordResetOTP
from apps.core.services.audit import log_action
from apps.core.mixins import ExamCoordinatorRequiredMixin
from django.views.generic import ListView, CreateView
from django.views import View
from django.urls import reverse_lazy

User = None  # Lazy import to avoid circular imports


def _get_user_model():
    global User
    if User is None:
        from django.contrib.auth import get_user_model
        User = get_user_model()
    return User


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Handle user login with role-based redirect."""
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Audit log
            log_action(
                request=request,
                user=user,
                action='login',
                model_name='User',
                object_id=user.pk,
                object_repr=str(user),
            )

            messages.success(request, f'Welcome back, {user.get_display_name()}!')

            # Redirect to next URL or role dashboard
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(user.get_dashboard_url())
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout."""
    log_action(
        request=request,
        action='logout',
        model_name='User',
        object_id=request.user.pk,
        object_repr=str(request.user),
    )
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    """Handle password change for authenticated users."""
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            log_action(
                request=request,
                action='password_change',
                model_name='User',
                object_id=user.pk,
                object_repr=str(user),
            )

            messages.success(request, 'Your password has been changed successfully.')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    """Handle password reset request — sends OTP email."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            UserModel = _get_user_model()
            users = UserModel.objects.filter(email=email, is_active=True)

            if users.exists():
                user = users.first()
                # Generate 6 digit OTP
                otp_code = get_random_string(length=6, allowed_chars='0123456789')
                expires_at = timezone.now() + timedelta(minutes=10)
                
                PasswordResetOTP.objects.create(
                    user=user,
                    otp_code=otp_code,
                    expires_at=expires_at
                )

                # Send email
                subject = 'EMS — Password Reset OTP'
                message = f"Your OTP for password reset is: {otp_code}. It will expire in 10 minutes."
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception:
                    pass

                log_action(
                    request=request,
                    user=user,
                    action='password_reset_otp_requested',
                    model_name='User',
                    object_id=user.pk,
                    object_repr=str(user),
                    details={'email': email},
                )
                
                request.session['reset_email'] = email
                return redirect('accounts:verify_otp')

            messages.success(
                request,
                'If an account with that email exists, a password reset OTP has been sent.'
            )
            # Even if email is not found, we redirect them to verify_otp to prevent email enumeration
            request.session['reset_email'] = email
            return redirect('accounts:verify_otp')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})

@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    """Verify the OTP sent to email."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        UserModel = _get_user_model()
        user = UserModel.objects.filter(email=email, is_active=True).first()
        
        if user:
            otp_obj = PasswordResetOTP.objects.filter(
                user=user, 
                otp_code=otp_code, 
                is_used=False,
                expires_at__gt=timezone.now()
            ).order_by('-created_at').first()
            
            if otp_obj:
                otp_obj.is_used = True
                otp_obj.save()
                request.session['otp_verified'] = True
                return redirect('accounts:reset_password_with_otp')
                
        messages.error(request, 'Invalid or expired OTP. Please try again.')
    
    return render(request, 'accounts/verify_otp.html', {'email': email})

@require_http_methods(["GET", "POST"])
def reset_password_with_otp_view(request):
    """Set new password after OTP verification."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    if not request.session.get('otp_verified'):
        return redirect('accounts:verify_otp')
        
    email = request.session.get('reset_email')
    UserModel = _get_user_model()
    user = UserModel.objects.filter(email=email, is_active=True).first()
    
    if not user:
        return redirect('accounts:forgot_password')
        
    if request.method == 'POST':
        form = ResetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            log_action(
                request=request,
                user=user,
                action='password_change',
                model_name='User',
                object_id=user.pk,
                object_repr=str(user),
                details={'via': 'otp_reset'},
            )
            # Clear session
            del request.session['reset_email']
            del request.session['otp_verified']
            
            messages.success(request, 'Your password has been reset. You can now log in.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm(user)

    return render(request, 'accounts/reset_password.html', {
        'form': form,
        'valid_link': True,
    })


@require_http_methods(["GET", "POST"])
def reset_password_view(request, uidb64, token):
    """Handle password reset using token from email."""
    UserModel = _get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = ResetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                log_action(
                    request=request,
                    user=user,
                    action='password_change',
                    model_name='User',
                    object_id=user.pk,
                    object_repr=str(user),
                    details={'via': 'reset_link'},
                )
                messages.success(request, 'Your password has been reset. You can now log in.')
                return redirect('accounts:login')
        else:
            form = ResetPasswordForm(user)

        return render(request, 'accounts/reset_password.html', {
            'form': form,
            'valid_link': True,
        })
    else:
        return render(request, 'accounts/reset_password.html', {
            'valid_link': False,
        })


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """Handle user profile viewing and editing."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_action(
                request=request,
                action='update',
                model_name='User',
                object_id=request.user.pk,
                object_repr=str(request.user),
                details={'fields': list(form.changed_data)},
            )
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

class UserListView(ExamCoordinatorRequiredMixin, ListView):
    """View for Admin and Exam Coordinators to list users."""
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        UserModel = _get_user_model()
        qs = UserModel.objects.exclude(is_superuser=True).order_by('first_name', 'last_name')
        # Exam Coordinators only see faculty; Admin sees everyone
        if not (self.request.user.is_admin_role or self.request.user.is_superuser):
            qs = qs.filter(role__in=['subject_coordinator', 'subject_faculty'])
        return qs

class UserCreateView(ExamCoordinatorRequiredMixin, CreateView):
    """View for Admin and Exam Coordinators to create new user accounts."""
    template_name = 'accounts/user_form.html'
    form_class = AdminUserCreateForm
    success_url = reverse_lazy('accounts:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['creator'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        # Auto-generate username from email
        user.username = user.email
        # Auto-generate password
        raw_password = get_random_string(length=12)
        user.set_password(raw_password)
        user.save()
        
        # Email the password to the user
        subject = 'Welcome to EMS - Your Account Details'
        message = f"Hello {user.get_display_name()},\n\nYour account has been created.\nLogin Email: {user.email}\nPassword: {raw_password}\n\nPlease log in and change your password immediately."
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception:
            messages.warning(self.request, "User created but failed to send welcome email.")
            
        messages.success(self.request, f"User {user.email} created successfully. Password emailed to user.")
        return super().form_valid(form)


class UserDeleteView(ExamCoordinatorRequiredMixin, View):
    """View for Admin and Exam Coordinators to delete user accounts."""

    def post(self, request, pk):
        UserModel = _get_user_model()
        user = UserModel.objects.filter(pk=pk).first()

        if not user:
            messages.error(request, "User not found.")
            return redirect('accounts:user_list')

        # Prevent deleting yourself or superusers
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('accounts:user_list')

        if user.is_superuser:
            messages.error(request, "Cannot delete a superuser account.")
            return redirect('accounts:user_list')

        # Exam coordinators can only delete faculty roles
        if not (request.user.is_admin_role or request.user.is_superuser):
            if user.role not in ('subject_coordinator', 'subject_faculty'):
                messages.error(request, "You don't have permission to delete this user.")
                return redirect('accounts:user_list')

        user_email = user.email
        log_action(
            request=request,
            action='delete',
            model_name='User',
            object_id=user.pk,
            object_repr=str(user),
        )
        user.delete()
        messages.success(request, f"User {user_email} has been deleted.")
        return redirect('accounts:user_list')
