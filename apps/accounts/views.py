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
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import (
    LoginForm, ChangePasswordForm, ForgotPasswordForm,
    ResetPasswordForm, UserProfileForm,
)
from apps.core.services.audit import log_action

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
    """Handle password reset request — sends reset email."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            UserModel = _get_user_model()
            users = UserModel.objects.filter(email=email, is_active=True)

            for user in users:
                # Generate reset token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                # Build reset URL
                reset_url = request.build_absolute_uri(
                    f'/accounts/reset-password/{uid}/{token}/'
                )

                # Send email
                subject = 'EMS — Password Reset Request'
                message = render_to_string('accounts/email/password_reset.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'app_name': 'EMS',
                })

                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception:
                    pass  # Don't reveal email sending status for security

                log_action(
                    request=request,
                    user=user,
                    action='password_reset',
                    model_name='User',
                    object_id=user.pk,
                    object_repr=str(user),
                    details={'email': email},
                )

            # Always show success (don't reveal if email exists)
            messages.success(
                request,
                'If an account with that email exists, a password reset link has been sent.'
            )
            return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


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
