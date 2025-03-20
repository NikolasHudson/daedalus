from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for the legal tech platform.
    Extends Django's built-in User model to allow for additional fields.
    """
    # Profile information
    phone_number = models.CharField(max_length=20, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=100, blank=True)
    
    # Preferences
    use_dark_mode = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.email or self.username