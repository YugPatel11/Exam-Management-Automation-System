"""
URL patterns for Question Papers.
"""
from django.urls import path
from apps.question_papers import views

app_name = 'question_papers'

urlpatterns = [
    path('', views.QuestionPaperListView.as_view(), name='list'),
    path('template/', views.QuestionPaperTemplateUpdateView.as_view(), name='template'),
    path('create/', views.QuestionPaperCreateView.as_view(), name='create'),
    path('<int:pk>/', views.QuestionPaperDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.QuestionPaperUpdateView.as_view(), name='edit'),
    path('<int:pk>/submit/', views.QuestionPaperSubmitView.as_view(), name='submit'),
    path('<int:pk>/preview/', views.QuestionPaperPreviewView.as_view(), name='preview'),
    path('<int:pk>/lock/', views.QuestionPaperLockView.as_view(), name='lock'),
    path('<int:pk>/print/', views.QuestionPaperPrintView.as_view(), name='print'),
    path('<int:pk>/pdf/', views.QuestionPaperPdfView.as_view(), name='pdf'),
    path('<int:pk>/co-btl/', views.COBTLReportView.as_view(), name='co_btl_report'),
]
