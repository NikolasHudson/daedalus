from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ClientCategory, Client, ClientContact, ClientDocument

@admin.register(ClientCategory)
class ClientCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 0
    fields = ('name', 'title', 'email', 'phone', 'is_primary')

class ClientDocumentInline(admin.TabularInline):
    model = ClientDocument
    extra = 0
    fields = ('document', 'document_type', 'added_by', 'added_at')
    readonly_fields = ('added_by', 'added_at')
    autocomplete_fields = ('document',)

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_type', 'category', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('client_type', 'is_active', 'category', 'data_classification', 'created_at')
    search_fields = ('name', 'email', 'phone', 'tax_id', 'notes')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'client_type', 'category', 'is_active')
        }),
        (_('Contact Information'), {
            'fields': ('email', 'phone', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        (_('Individual Details'), {
            'fields': ('date_of_birth', 'ssn_last_four'),
            'classes': ('collapse',),
            'description': _('These fields apply only to individual clients')
        }),
        (_('Organization Details'), {
            'fields': ('tax_id', 'industry'),
            'classes': ('collapse',),
            'description': _('These fields apply only to organization clients')
        }),
        (_('Client Status'), {
            'fields': ('intake_date', 'referral_source', 'notes')
        }),
        (_('Security Classification'), {
            'fields': ('is_confidential', 'data_classification'),
            'description': _('These settings control access restrictions to this client')
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('uuid', 'created_by', 'updated_by', 'created_at', 'updated_at')
    inlines = [ClientContactInline, ClientDocumentInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, 'added_by') and not instance.added_by:
                instance.added_by = request.user
            instance.save()
        formset.save_m2m()

@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'title', 'email', 'phone', 'is_primary')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('name', 'email', 'phone', 'client__name')
    autocomplete_fields = ('client',)