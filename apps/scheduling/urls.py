"""
URL patterns for Exam Scheduling.
"""
from django.urls import path
from apps.scheduling import views

app_name = 'scheduling'

urlpatterns = [
    path('', views.ScheduleDashboardView.as_view(), name='dashboard'),
    path('manager/<int:exam_id>/', views.ScheduleManagerView.as_view(), name='manager'),
]
