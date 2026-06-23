"""
URL patterns for Question Papers.
"""
from django.urls import path
from apps.question_papers import views

app_name = 'question_papers'

urlpatterns = [
    path('', views.QuestionPaperListView.as_view(), name='list'),
    path('create/', views.QuestionPaperCreateView.as_view(), name='create'),
    path('<int:pk>/', views.QuestionPaperDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.QuestionPaperUpdateView.as_view(), name='edit'),
    path('<int:pk>/submit/', views.QuestionPaperSubmitView.as_view(), name='submit'),
]
