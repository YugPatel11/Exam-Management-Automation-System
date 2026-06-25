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
    path('division/<int:exam_id>/', views.DivisionAnalysisView.as_view(), name='division'),
    path('faculty/<int:exam_id>/', views.FacultyAnalysisView.as_view(), name='faculty'),
    path('component/<int:exam_id>/', views.ComponentAnalysisView.as_view(), name='component'),
    path('co/<int:exam_id>/', views.COAnalysisView.as_view(), name='co'),
    path('btl/<int:exam_id>/', views.BTLAnalysisView.as_view(), name='btl'),
]
