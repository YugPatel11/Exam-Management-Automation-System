"""
URL patterns for Student Management.
"""
from django.urls import path
from apps.students import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('import/', views.ImportWizardView.as_view(), name='import_wizard'),
    path('import/preview/', views.ImportPreviewView.as_view(), name='import_preview'),
    path('import/process/', views.ImportProcessView.as_view(), name='import_process'),
]
