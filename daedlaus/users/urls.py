from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    # Login and logout
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Password reset
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Password change
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
    
    # Theme preference
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
]