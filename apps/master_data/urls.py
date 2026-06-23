"""
URL patterns for Master Data management.
"""
from django.urls import path
from apps.master_data import views

app_name = 'master_data'

urlpatterns = [
    # Programs
    path('programs/', views.ProgramListView.as_view(), name='program_list'),
    path('programs/add/', views.ProgramCreateView.as_view(), name='program_create'),
    path('programs/<uuid:pk>/edit/', views.ProgramUpdateView.as_view(), name='program_update'),
    path('programs/<uuid:pk>/delete/', views.ProgramDeleteView.as_view(), name='program_delete'),

    # Subjects
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/add/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('subjects/<uuid:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_update'),
    path('subjects/<uuid:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    # Divisions
    path('divisions/', views.DivisionListView.as_view(), name='division_list'),
    path('divisions/add/', views.DivisionCreateView.as_view(), name='division_create'),
    path('divisions/<uuid:pk>/edit/', views.DivisionUpdateView.as_view(), name='division_update'),
    path('divisions/<uuid:pk>/delete/', views.DivisionDeleteView.as_view(), name='division_delete'),

    # Classrooms
    path('classrooms/', views.ClassroomListView.as_view(), name='classroom_list'),
    path('classrooms/add/', views.ClassroomCreateView.as_view(), name='classroom_create'),
    path('classrooms/<uuid:pk>/edit/', views.ClassroomUpdateView.as_view(), name='classroom_update'),
    path('classrooms/<uuid:pk>/delete/', views.ClassroomDeleteView.as_view(), name='classroom_delete'),
]
