"""
URL patterns for Marks Management.
"""
from django.urls import path
from apps.marks import views

app_name = 'marks'

urlpatterns = [
    # Coordinator Allocation
    path('allocation/', views.MarksAllocationDashboardView.as_view(), name='allocation_dashboard'),
    path('allocation/<int:exam_id>/', views.MarksAllocationManagerView.as_view(), name='allocation_manager'),
    
    # Coordinator Review
    path('review/', views.MarksReviewDashboardView.as_view(), name='review_dashboard'),
    path('review/<int:pk>/', views.MarksReviewDetailView.as_view(), name='review_detail'),
    
    # Faculty Entry
    path('tasks/', views.MarksEntryListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.MarksEntryFormView.as_view(), name='entry_form'),
    path('tasks/<int:pk>/upload/', views.MarksCsvUploadView.as_view(), name='csv_upload'),
    path('tasks/<int:pk>/sample-csv/', views.MarksCsvSampleView.as_view(), name='sample_csv'),
]
