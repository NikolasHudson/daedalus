from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView
)
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from .forms import CustomUserCreationForm, CustomUserChangeForm, UserPreferencesForm


class CustomLoginView(LoginView):
    """Custom login view using our template."""
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    

class CustomLogoutView(LogoutView):
    """Custom logout view."""
    next_page = 'login'
    http_method_names = ['get', 'post']  # Allow both GET and POST methods


class RegisterView(CreateView):
    """User registration view."""
    form_class = CustomUserCreationForm
    template_name = 'auth/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        """Log the user in after they register."""
        response = super().form_valid(form)
        # Auto-login after registration
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return redirect('home')  # Redirect to home page after registration
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect to home if already authenticated."""
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ProfileView(UpdateView):
    """User profile view."""
    form_class = CustomUserChangeForm
    template_name = 'auth/profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self, queryset=None):
        """Get the current logged-in user."""
        return self.request.user


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with custom templates."""
    template_name = 'auth/password_reset_form.html'
    email_template_name = 'emails/password_reset_email.txt'
    html_email_template_name = 'emails/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view with custom template."""
    template_name = 'auth/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view with custom template."""
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view with custom template."""
    template_name = 'auth/password_reset_complete.html'


@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeView(PasswordChangeView):
    """Custom password change view with custom template."""
    template_name = 'auth/password_change_form.html'
    success_url = reverse_lazy('password_change_done')


@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    """Custom password change done view with custom template."""
    template_name = 'auth/password_change_done.html'


@require_POST
@login_required
def toggle_theme(request):
    """Toggle theme between light and dark mode."""
    user = request.user
    user.use_dark_mode = not user.use_dark_mode
    user.save()
    
    # Return an HTMX response that triggers a refresh of the page
    response = HttpResponse()
    response["HX-Refresh"] = "true"
    return response