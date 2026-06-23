"""
URL patterns for Seating Arrangement.
"""
from django.urls import path
from apps.seating import views

app_name = 'seating'

urlpatterns = [
    path('', views.SeatingDashboardView.as_view(), name='dashboard'),
    path('manager/<int:exam_id>/', views.SeatingManagerView.as_view(), name='manager'),
]
