from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .models import S3Configuration, BedrockConfiguration


class AWSCredentialsAdmin(admin.ModelAdmin):
    """
    Base admin class for AWS credential management.
    """
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'validation_status')
    list_display = ('name', 'region', 'is_active', 'created_at', 'updated_at', 'validation_badge')
    list_filter = ('is_active', 'region', 'created_at', 'updated_at')
    search_fields = ('name',)
    save_on_top = True
    
    def has_import_permission(self, request):
        return False  # Disable import for security reasons
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Only show created_by and updated_by fields in the admin interface if they have values
        if obj:
            if not obj.created_by:
                form.base_fields.pop('created_by', None)
            if not obj.updated_by:
                form.base_fields.pop('updated_by', None)
        else:
            form.base_fields.pop('created_by', None)
            form.base_fields.pop('updated_by', None)
        return form
    
    def validation_status(self, obj):
        """Display the validation status with a button to revalidate."""
        if not obj.pk:
            return _("Save configuration first to validate")
        
        try:
            url = reverse('aws:validate_aws_credentials', args=[obj._meta.app_label, obj._meta.model_name, obj.pk])
            button_html = format_html(
                '<a href="{}" class="button validation-button">Validate Now</a>',
                url
            )
        except:
            button_html = format_html(
                '<span class="button validation-button" style="opacity: 0.5;">Validate Now (URL Error)</span>'
            )
        
        try:
            # Perform validation
            success, message = obj.validate_credentials()
            
            if success:
                status_html = format_html(
                    '<span style="color: green; font-weight: bold;">✓ Valid</span>'
                )
            else:
                status_html = format_html(
                    '<span style="color: red; font-weight: bold;">✗ Invalid</span>'
                )
            
            return format_html(
                '{} {}<br><div style="margin-top: 5px; font-size: 0.9em;">{}</div>',
                status_html, button_html, message
            )
        except Exception as e:
            return format_html(
                '<span style="color: red; font-weight: bold;">Error during validation</span> {}<br><div style="margin-top: 5px; font-size: 0.9em; color: red;">{}</div>',
                button_html, str(e)
            )
    
    validation_status.short_description = _("Validation Status")
    
    def validation_badge(self, obj):
        """A simple badge for the list view."""
        try:
            success, _ = obj.validate_credentials()
            if success:
                return format_html('<span style="color: green; font-weight: bold;">✓</span>')
            else:
                return format_html('<span style="color: red; font-weight: bold;">✗</span>')
        except:
            return format_html('<span style="color: gray; font-weight: bold;">?</span>')
    
    validation_badge.short_description = _("Valid")
    
    def save_model(self, request, obj, form, change):
        """Save model with user tracking."""
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/aws_admin.css',)
        }
        js = ('admin/js/aws_admin.js',)


@admin.register(S3Configuration)
class S3ConfigurationAdmin(AWSCredentialsAdmin):
    """Admin interface for S3 configuration."""
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        (_('AWS Credentials'), {
            'fields': ('aws_access_key_id', 'aws_secret_access_key', 'region')
        }),
        (_('S3 Settings'), {
            'fields': ('bucket_name', 'use_for_static_files', 'use_for_media_files', 
                      'create_bucket_if_not_exists', 'custom_domain')
        }),
        (_('Validation'), {
            'fields': ('validation_status',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    list_display = ('name', 'bucket_name', 'region', 'is_active', 
                   'use_for_static_files', 'use_for_media_files', 'validation_badge')


@admin.register(BedrockConfiguration)
class BedrockConfigurationAdmin(AWSCredentialsAdmin):
    """Admin interface for Bedrock configuration."""
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        (_('AWS Credentials'), {
            'fields': ('aws_access_key_id', 'aws_secret_access_key', 'region')
        }),
        (_('Bedrock Settings'), {
            'fields': ('default_model_id',)
        }),
        (_('Validation'), {
            'fields': ('validation_status',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    list_display = ('name', 'region', 'default_model_id', 'is_active', 'validation_badge')