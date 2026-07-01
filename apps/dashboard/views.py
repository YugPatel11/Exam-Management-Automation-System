"""
Dashboard views — role-based routing to appropriate dashboards.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from apps.accounts.models import User
from apps.exams.models import Exam
from apps.master_data.models import Subject, Program, Classroom
from apps.students.models import Student
from apps.marks.models import MarksEntryTask
from apps.duty_chart.models import DutyAssignment
from apps.core.models_audit import AuditLog


@login_required
def dashboard_home(request):
    """Redirect to the appropriate role-based dashboard."""
    return redirect(request.user.get_dashboard_url())


@login_required
def admin_dashboard(request):
    """Admin dashboard with institute-wide overview."""
    if not (request.user.role in ('admin',) or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())

    # Stats
    user_count = User.objects.filter(is_active=True).count()
    program_count = Program.objects.count()
    subject_count = Subject.objects.count()
    student_count = Student.objects.count()
    exam_count = Exam.objects.count()
    classroom_count = Classroom.objects.count()

    # Recent audit logs
    try:
        recent_logs = AuditLog.objects.select_related('user').order_by('-created_at')[:10]
    except Exception:
        recent_logs = []

    # Active exams
    active_exams = Exam.objects.filter(status='active').order_by('-start_date')[:5]

    context = {
        'page_title': 'Admin Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
        'user_count': user_count,
        'program_count': program_count,
        'subject_count': subject_count,
        'student_count': student_count,
        'exam_count': exam_count,
        'classroom_count': classroom_count,
        'recent_logs': recent_logs,
        'active_exams': active_exams,
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def coordinator_dashboard(request):
    """Exam Coordinator dashboard with exam workflow overview."""
    if not (request.user.role in ('admin', 'exam_coordinator') or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())

    # All exams with status overview
    exams = Exam.objects.all().order_by('-start_date')[:10]

    # Build workflow status for each exam
    exam_workflows = []
    for exam in exams:
        workflow = {
            'exam': exam,
            'has_schedule': hasattr(exam, 'schedules') and exam.schedules.exists() if hasattr(exam, 'schedules') else False,
            'has_seating': hasattr(exam, 'seating_plan'),
            'has_duty_chart': hasattr(exam, 'duty_chart'),
            'has_reports': exam.reports.exists() if hasattr(exam, 'reports') else False,
        }
        # Count marks tasks
        try:
            tasks = MarksEntryTask.objects.filter(exam=exam)
            workflow['total_tasks'] = tasks.count()
            workflow['submitted_tasks'] = tasks.filter(status__in=['submitted', 'locked']).count()
        except Exception:
            workflow['total_tasks'] = 0
            workflow['submitted_tasks'] = 0
        exam_workflows.append(workflow)

    context = {
        'page_title': 'Exam Coordinator Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
        'exam_workflows': exam_workflows,
        'total_exams': Exam.objects.count(),
        'active_exams': Exam.objects.filter(status='active').count(),
    }
    return render(request, 'dashboard/exam_coordinator.html', context)


@login_required
def subject_coordinator_dashboard(request):
    """Subject Coordinator dashboard with assigned subjects overview."""
    if not (request.user.role in ('admin', 'exam_coordinator', 'subject_coordinator') or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())

    # Get subjects coordinated by this user
    from apps.academic.models import FacultyTeachingAssignment
    coordinated = FacultyTeachingAssignment.objects.filter(
        faculty__user=request.user,
        is_coordinator=True
    ).select_related('semester_subject__subject', 'semester')

    # Group by semester
    exam_subjects = {}
    for c in coordinated:
        if c.semester not in exam_subjects:
            exam_subjects[c.semester] = []
        # Ensure distinct subjects are added
        if c.semester_subject.subject not in exam_subjects[c.semester]:
            exam_subjects[c.semester].append(c.semester_subject.subject)

    # Question paper stats
    from apps.question_papers.models import QuestionPaper
    qp_count = QuestionPaper.objects.filter(created_by=request.user).count()
    qp_submitted = QuestionPaper.objects.filter(created_by=request.user, status='submitted').count()

    context = {
        'page_title': 'Subject Coordinator Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
        'exam_subjects': exam_subjects,
        'qp_count': qp_count,
        'qp_submitted': qp_submitted,
        'total_coordinated': coordinated.count(),
    }
    return render(request, 'dashboard/subject_coordinator.html', context)


@login_required
def faculty_dashboard(request):
    """Subject Faculty dashboard with duties and marks entry."""
    # Marks entry tasks assigned to this faculty
    tasks = MarksEntryTask.objects.filter(
        faculty=request.user
    ).select_related('exam', 'subject', 'teaching_assignment').order_by('-exam__start_date')

    pending_tasks = tasks.filter(status='pending')
    submitted_tasks = tasks.filter(status__in=['submitted', 'locked'])

    # Duty assignments
    duties = DutyAssignment.objects.filter(
        faculty=request.user
    ).select_related('classroom').order_by('date', 'start_time')[:10]

    context = {
        'page_title': 'Faculty Dashboard',
        'breadcrumbs': [{'label': 'Dashboard', 'url': None}],
        'pending_tasks': pending_tasks,
        'submitted_tasks': submitted_tasks,
        'total_tasks': tasks.count(),
        'duties': duties,
    }
    return render(request, 'dashboard/subject_faculty.html', context)
