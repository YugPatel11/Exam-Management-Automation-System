"""
URL patterns for Academic Year Management.
"""
from django.urls import path
from apps.academic import views

app_name = 'academic'

urlpatterns = [
    # Academic Year CRUD
    path('', views.AcademicYearListView.as_view(), name='year_list'),
    path('create/', views.AcademicYearCreateView.as_view(), name='year_create'),
    path('<int:pk>/', views.AcademicYearDetailView.as_view(), name='year_detail'),
    path('<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='year_update'),
    path('<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='year_delete'),

    # Import Wizard
    path('<int:pk>/import/', views.ImportWizardUploadView.as_view(), name='import_upload'),
    path('<int:pk>/import/preview/', views.ImportWizardPreviewView.as_view(), name='import_preview'),
    path('<int:pk>/import/process/', views.ImportWizardProcessView.as_view(), name='import_process'),

    # Semester Detail
    path('semester/<int:pk>/', views.SemesterDetailView.as_view(), name='semester_detail'),

    # API endpoints for cascading dropdowns
    path('api/<int:pk>/semesters/', views.SemesterListAPIView.as_view(), name='api_semesters'),
    path('api/semester/<int:pk>/subjects/', views.SemesterSubjectsAPIView.as_view(), name='api_semester_subjects'),
]
