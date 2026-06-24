"""
Dashboard views — role-based routing to appropriate dashboards.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def dashboard_home(request):
    """Redirect to the appropriate role-based dashboard."""
    return redirect(request.user.get_dashboard_url())


@login_required
def admin_dashboard(request):
    """Admin dashboard with institute-wide overview."""
    if not (request.user.role in ('admin',) or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())

    context = {
        'page_title': 'Admin Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def coordinator_dashboard(request):
    """Exam Coordinator dashboard with exam workflow overview."""
    if not (request.user.role in ('admin', 'exam_coordinator') or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())

    context = {
        'page_title': 'Exam Coordinator Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
    }
    return render(request, 'dashboard/exam_coordinator.html', context)


@login_required
def subject_coordinator_dashboard(request):
    """Subject Coordinator dashboard with assigned subjects overview."""
    if not (request.user.role in ('admin', 'exam_coordinator', 'subject_coordinator') or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())

    context = {
        'page_title': 'Subject Coordinator Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
    }
    return render(request, 'dashboard/subject_coordinator.html', context)


@login_required
def faculty_dashboard(request):
    """Subject Faculty dashboard with duties and marks entry."""
    context = {
        'page_title': 'Faculty Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
    }
    return render(request, 'dashboard/subject_faculty.html', context)
