"""
URL patterns for Result Analysis.
"""
from django.urls import path
from apps.analysis import views

app_name = 'analysis'

urlpatterns = [
    path('', views.AnalysisDashboardView.as_view(), name='dashboard'),
    path('program/<int:exam_id>/', views.ProgramAnalysisView.as_view(), name='program'),
    path('subject/<int:exam_id>/', views.SubjectAnalysisView.as_view(), name='subject'),
]
