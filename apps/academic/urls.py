"""
URL patterns for Academic Year Management.
Includes Academic Structure, Faculty Master, and Teaching Allocation.
"""
from django.urls import path
from apps.academic import views
from apps.academic import faculty_views

app_name = 'academic'

urlpatterns = [
    # Academic Year CRUD
    path('', views.AcademicYearListView.as_view(), name='year_list'),
    path('create/', views.AcademicYearCreateView.as_view(), name='year_create'),
    path('<int:pk>/', views.AcademicYearDetailView.as_view(), name='year_detail'),
    path('<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='year_update'),
    path('<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='year_delete'),

    # Academic Structure Import Wizard
    path('<int:pk>/import/', views.ImportWizardUploadView.as_view(), name='import_upload'),
    path('<int:pk>/import/preview/', views.ImportWizardPreviewView.as_view(), name='import_preview'),
    path('<int:pk>/import/process/', views.ImportWizardProcessView.as_view(), name='import_process'),

    # Semester Detail
    path('semester/<int:pk>/', views.SemesterDetailView.as_view(), name='semester_detail'),

    # ─── Faculty Master ───
    path('<int:pk>/faculty/', faculty_views.FacultyMasterListView.as_view(), name='faculty_list'),
    path('<int:pk>/faculty/<int:fac_pk>/edit/', faculty_views.FacultyMasterEditView.as_view(), name='faculty_edit'),
    path('<int:pk>/faculty/<int:fac_pk>/delete/', faculty_views.FacultyMasterDeleteView.as_view(), name='faculty_delete'),
    path('<int:pk>/faculty/import/', faculty_views.FacultyMasterImportUploadView.as_view(), name='faculty_import_upload'),
    path('<int:pk>/faculty/import/preview/', faculty_views.FacultyMasterImportPreviewView.as_view(), name='faculty_import_preview'),
    path('<int:pk>/faculty/import/process/', faculty_views.FacultyMasterImportProcessView.as_view(), name='faculty_import_process'),

    # ─── Teaching Allocation ───
    path('<int:pk>/allocation/', faculty_views.TeachingAllocationListView.as_view(), name='allocation_list'),
    path('<int:pk>/allocation/<int:alloc_pk>/delete/', faculty_views.TeachingAllocationDeleteView.as_view(), name='allocation_delete'),
    path('<int:pk>/allocation/import/', faculty_views.AllocationImportUploadView.as_view(), name='allocation_import_upload'),
    path('<int:pk>/allocation/import/preview/', faculty_views.AllocationImportPreviewView.as_view(), name='allocation_import_preview'),
    path('<int:pk>/allocation/import/process/', faculty_views.AllocationImportProcessView.as_view(), name='allocation_import_process'),

    # ─── API endpoints ───
    path('api/<int:pk>/semesters/', views.SemesterListAPIView.as_view(), name='api_semesters'),
    path('api/semester/<int:pk>/subjects/', views.SemesterSubjectsAPIView.as_view(), name='api_semester_subjects'),
    path('api/<int:pk>/subject/<int:ss_pk>/faculty/', faculty_views.SubjectFacultyAPIView.as_view(), name='api_subject_faculty'),
]
