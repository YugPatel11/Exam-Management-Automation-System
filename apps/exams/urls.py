"""
URL patterns for Exam Management.
"""
from django.urls import path
from apps.exams import views

app_name = 'exams'

urlpatterns = [
    path('', views.ExamListView.as_view(), name='exam_list'),
    path('<uuid:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('<uuid:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
]
