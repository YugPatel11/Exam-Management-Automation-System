"""
URL patterns for the dashboard app.
"""
from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('coordinator/', views.coordinator_dashboard, name='coordinator'),
    path('subject-coordinator/', views.subject_coordinator_dashboard, name='subject_coordinator'),
    path('faculty/', views.faculty_dashboard, name='faculty'),
]
