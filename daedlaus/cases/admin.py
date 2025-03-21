from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import CaseCategory, Case, Matter, CaseFolder, CaseDocument

@admin.register(CaseCategory)
class CaseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    ordering = ('name',)

class MatterInline(admin.TabularInline):
    model = Matter
    extra = 0
    fields = ('name', 'description', 'is_active', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')

class CaseFolderInline(admin.TabularInline):
    model = CaseFolder
    extra = 0
    fields = ('name', 'parent', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')
    fk_name = 'case'

class CaseDocumentInline(admin.TabularInline):
    model = CaseDocument
    extra = 0
    fields = ('document', 'folder', 'matter', 'added_by', 'added_at')
    readonly_fields = ('added_by', 'added_at')
    autocomplete_fields = ('document',)

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'case_number', 'category', 'status', 'get_client_name', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'case_number', 'client_name', 'client__name')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'case_number', 'category', 'status', 'description')
        }),
        (_('Client Information'), {
            'fields': ('client', 'client_name', 'client_email', 'client_phone')
        }),
        (_('Dates'), {
            'fields': ('filed_date',)
        }),
        (_('Team'), {
            'fields': ('assigned_attorneys',)
        }),
        (_('Portal Settings'), {
            'fields': ('is_portal_enabled', 'portal_title', 'portal_description'),
            'classes': ('collapse',),
            'description': _('These settings control how this case appears in the Co-Counsel Portal')
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('uuid', 'created_by', 'updated_by', 'created_at', 'updated_at')
    inlines = [MatterInline, CaseFolderInline, CaseDocumentInline]
    filter_horizontal = ('assigned_attorneys',)
    autocomplete_fields = ('client',)
    
    def get_client_name(self, obj):
        if obj.client:
            return obj.client.name
        return obj.client_name
    get_client_name.short_description = 'Client'
    get_client_name.admin_order_field = 'client__name'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, 'created_by') and not instance.created_by:
                instance.created_by = request.user
            if hasattr(instance, 'added_by') and not instance.added_by:
                instance.added_by = request.user
            instance.save()
        formset.save_m2m()

@admin.register(Matter)
class MatterAdmin(admin.ModelAdmin):
    list_display = ('name', 'case', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'case__title')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(CaseFolder)
class CaseFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'case', 'matter', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'case__title')
    readonly_fields = ('created_by', 'created_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)