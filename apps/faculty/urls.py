"""
URL patterns for Faculty Assignment Management.
"""
from django.urls import path
from apps.faculty import views

app_name = 'faculty'

urlpatterns = [
    path('', views.AssignmentListView.as_view(), name='assignment_list'),
    
    # Coordinator Import
    path('import/coordinator/', views.CoordinatorImportWizardView.as_view(), name='coordinator_import_wizard'),
    path('import/coordinator/preview/', views.CoordinatorImportPreviewView.as_view(), name='coordinator_import_preview'),
    path('import/coordinator/process/', views.CoordinatorImportProcessView.as_view(), name='coordinator_import_process'),
    
    # Faculty Import
    path('import/faculty/', views.FacultyImportWizardView.as_view(), name='faculty_import_wizard'),
    path('import/faculty/preview/', views.FacultyImportPreviewView.as_view(), name='faculty_import_preview'),
    path('import/faculty/process/', views.FacultyImportProcessView.as_view(), name='faculty_import_process'),
]
