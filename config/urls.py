"""
Root URL configuration for EMS project.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Root redirects to login
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='root'),

    # Academic Year Management (new primary workflow)
    path('academic/', include('apps.academic.urls', namespace='academic')),

    # Authentication
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # Dashboard
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),

    # Master Data
    path('master-data/', include('apps.master_data.urls', namespace='master_data')),

    # Exams
    path('exams/', include('apps.exams.urls', namespace='exams')),

    # Students
    path('students/', include('apps.students.urls', namespace='students')),

    # Curriculum
    path('curriculum/', include('apps.curriculum.urls', namespace='curriculum')),



    # Assessment Schemes
    path('assessment/', include('apps.assessment.urls', namespace='assessment')),

    # Scheduling
    path('scheduling/', include('apps.scheduling.urls', namespace='scheduling')),

    # Question Papers
    path('question-papers/', include('apps.question_papers.urls', namespace='question_papers')),

    # Seating
    path('seating/', include('apps.seating.urls', namespace='seating')),

    # Duty Chart
    path('duty-chart/', include('apps.duty_chart.urls', namespace='duty_chart')),

    # Marks
    path('marks/', include('apps.marks.urls', namespace='marks')),

    # Analysis
    path('analysis/', include('apps.analysis.urls', namespace='analysis')),

    # Reports
    path('reports/', include('apps.reports.urls', namespace='reports')),

    # API v1
    path('api/v1/', include([
        path('accounts/', include('apps.accounts.api_urls', namespace='api-accounts')),
    ])),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site
admin.site.site_header = 'EMS Administration'
admin.site.site_title = 'EMS Admin'
admin.site.index_title = 'Exam Management System'
