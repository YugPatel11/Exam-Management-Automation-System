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

    # Faculty
    path('faculty/', include('apps.faculty.urls', namespace='faculty')),

    # Assessment Schemes
    path('assessment/', include('apps.assessment.urls', namespace='assessment')),

    # Scheduling
    path('scheduling/', include('apps.scheduling.urls', namespace='scheduling')),

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
