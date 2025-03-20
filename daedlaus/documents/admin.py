from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    DocumentCategory, 
    Document, 
    DocumentVersion, 
    DocumentComment,
    DocumentAccess
)

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    ordering = ('name',)
    

class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ('version_number', 'file_name', 'file_size', 'file_type', 'uploaded_by', 'uploaded_at')
    fields = ('version_number', 'file', 'file_name', 'file_size', 'notes', 'uploaded_by', 'uploaded_at')
    can_delete = False
    max_num = 0  # Don't allow adding new versions through the admin
    
    def has_add_permission(self, request, obj=None):
        return False


class DocumentCommentInline(admin.TabularInline):
    model = DocumentComment
    extra = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'text', 'created_at')


class DocumentAccessInline(admin.TabularInline):
    model = DocumentAccess
    extra = 1
    fields = ('user', 'access_type', 'granted_by', 'expires_at')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'created_by', 'created_at', 'version_count', 'document_link')
    list_filter = ('status', 'category', 'is_private', 'created_at')
    search_fields = ('title', 'description', 'tags')
    readonly_fields = ('uuid', 'created_by', 'updated_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'tags', 'status')
        }),
        (_('Security'), {
            'fields': ('is_private',)
        }),
        (_('Metadata'), {
            'fields': ('uuid', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [DocumentVersionInline, DocumentAccessInline, DocumentCommentInline]
    
    def version_count(self, obj):
        count = obj.versions.count()
        return count
    version_count.short_description = _('Versions')
    
    def document_link(self, obj):
        """Generate a link to the current version if available"""
        if obj.current_version:
            url = reverse('admin:documents_documentversion_change', args=[obj.current_version.id])
            return format_html('<a href="{}">{} (v{})</a>', 
                             url, obj.current_version.file_name, obj.current_version.version_number)
        return '-'
    document_link.short_description = _('Current Version')
    
    def save_model(self, request, obj, form, change):
        """Override save_model to set created_by and updated_by"""
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        """Override save_formset to set uploaded_by for document versions"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, DocumentVersion) and not instance.uploaded_by:
                instance.uploaded_by = request.user
            if isinstance(instance, DocumentComment) and not instance.user:
                instance.user = request.user
            if isinstance(instance, DocumentAccess) and not instance.granted_by:
                instance.granted_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'document', 'version_number', 'file_name', 'file_size_display', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('document__title', 'file_name')
    readonly_fields = ('document', 'version_number', 'uploaded_by', 'uploaded_at', 'file_name', 'file_size', 'file_type')
    fields = ('document', 'version_number', 'file', 'file_name', 'file_size_display', 'file_type', 'notes', 'uploaded_by', 'uploaded_at', 's3_key')
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.file_size:
            # Convert to KB, MB, etc.
            size = obj.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024 or unit == 'GB':
                    break
                size /= 1024
            return f"{size:.2f} {unit}"
        return '0 B'
    file_size_display.short_description = _('File Size')
    
    def has_add_permission(self, request):
        """Disable adding versions directly through admin"""
        return False