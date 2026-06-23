"""
URL patterns for Assessment Scheme Configuration.
"""
from django.urls import path
from apps.assessment import views

app_name = 'assessment'

urlpatterns = [
    path('', views.CoordinatorDashboardView.as_view(), name='dashboard'),
    path('builder/<int:subject_id>/<str:parent_type>/', views.SchemeBuilderView.as_view(), name='builder'),
]
