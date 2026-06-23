"""
URL patterns for Curriculum Management.
"""
from django.urls import path
from apps.curriculum import views

app_name = 'curriculum'

urlpatterns = [
    path('', views.CurriculumListView.as_view(), name='scheme_list'),
    path('import/', views.ImportWizardView.as_view(), name='import_wizard'),
    path('import/preview/', views.ImportPreviewView.as_view(), name='import_preview'),
    path('import/process/', views.ImportProcessView.as_view(), name='import_process'),
]
