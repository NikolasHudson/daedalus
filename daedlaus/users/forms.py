from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users with our custom User model."""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users with our custom User model."""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                  'job_title', 'organization', 'use_dark_mode')


class UserPreferencesForm(forms.ModelForm):
    """Form for updating user preferences."""
    
    class Meta:
        model = User
        fields = ('use_dark_mode',)