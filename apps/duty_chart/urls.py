"""
URL patterns for Duty Chart.
"""
from django.urls import path
from apps.duty_chart import views

app_name = 'duty_chart'

urlpatterns = [
    path('', views.DutyChartDashboardView.as_view(), name='dashboard'),
    path('manager/<int:exam_id>/', views.DutyChartManagerView.as_view(), name='manager'),
]
