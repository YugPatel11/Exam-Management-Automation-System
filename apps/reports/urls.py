"""
URL patterns for Reports Management.
"""
from django.urls import path
from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    path('manager/<int:exam_id>/', views.ReportManagerView.as_view(), name='manager'),
    path('download/<int:report_id>/', views.ReportDownloadView.as_view(), name='download'),
]
