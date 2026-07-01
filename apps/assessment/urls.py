"""
URL patterns for Assessment Scheme Configuration.
"""
from django.urls import path
from apps.assessment import views

app_name = 'assessment'

urlpatterns = [
    path('', views.CoordinatorDashboardView.as_view(), name='dashboard'),
    path('builder/<int:component_id>/', views.SchemeBuilderView.as_view(), name='builder'),
]
