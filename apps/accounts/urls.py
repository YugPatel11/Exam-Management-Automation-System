"""
URL patterns for the accounts app.
"""
from django.urls import path
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('forgot-password/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('forgot-password/set-new-password/', views.reset_password_with_otp_view, name='reset_password_with_otp'),
    path('profile/', views.profile_view, name='profile'),
    
    # User Management for Exam Coordinators
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/import/', views.UserCsvUploadView.as_view(), name='user_import'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
]
