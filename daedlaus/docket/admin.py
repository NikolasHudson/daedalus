from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Court, Docket, Party, Attorney, DocketEntry

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'jurisdiction', 'city', 'state')
    list_filter = ('level', 'state', 'e_filing_available')
    search_fields = ('name', 'jurisdiction', 'city', 'state')
    fieldsets = (
        (None, {
            'fields': ('name', 'level', 'jurisdiction')
        }),
        (_('Location'), {
            'fields': ('address', 'city', 'state', 'postal_code')
        }),
        (_('Contact Information'), {
            'fields': ('website', 'phone')
        }),
        (_('Electronic Filing'), {
            'fields': ('e_filing_available', 'e_filing_url')
        }),
        (_('System Codes'), {
            'fields': ('pacer_code',)
        }),
    )

class PartyInline(admin.TabularInline):
    model = Party
    extra = 1
    fields = ('type', 'name', 'client', 'extra_info', 'date_terminated')
    autocomplete_fields = ('client',)

class DocketEntryInline(admin.TabularInline):
    model = DocketEntry
    extra = 1
    fields = ('date_filed', 'document_number', 'description', 'document')
    autocomplete_fields = ('document',)
    show_change_link = True

@admin.register(Docket)
class DocketAdmin(admin.ModelAdmin):
    list_display = ('case_name', 'docket_number', 'court', 'date_filed', 'assigned_to', 'is_active')
    list_filter = ('court', 'date_filed', 'date_terminated')
    search_fields = ('case_name', 'docket_number', 'assigned_to')
    
    fieldsets = (
        (None, {
            'fields': ('case', 'court', 'docket_number', 'case_name')
        }),
        (_('Dates'), {
            'fields': ('date_filed', 'date_terminated', 'date_converted', 'date_discharged')
        }),
        (_('Assignment'), {
            'fields': ('assigned_to', 'referred_to')
        }),
        (_('Case Details'), {
            'fields': ('cause', 'nature_of_suit', 'jury_demand', 'demand', 'jurisdiction', 'mdl_status')
        }),
        (_('Federal Information'), {
            'fields': ('federal_office_code', 'federal_case_type', 'federal_judge_initials_assigned', 
                      'federal_judge_initials_referred', 'federal_defendant_number'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [PartyInline, DocketEntryInline]
    autocomplete_fields = ('case',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, DocketEntry):
                if not instance.created_by_id:
                    instance.created_by = request.user
                instance.updated_by = request.user
            instance.save()
        formset.save_m2m()

class AttorneyInline(admin.TabularInline):
    model = Attorney
    extra = 1
    fields = ('name', 'roles', 'contact', 'user')
    autocomplete_fields = ('user',)

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'docket', 'client')
    list_filter = ('type', 'docket__court')
    search_fields = ('name', 'docket__case_name', 'docket__docket_number')
    autocomplete_fields = ('docket', 'client')
    inlines = [AttorneyInline]

@admin.register(Attorney)
class AttorneyAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'user')
    list_filter = ('party__docket__court',)
    search_fields = ('name', 'contact', 'party__name')
    autocomplete_fields = ('party', 'user')

@admin.register(DocketEntry)
class DocketEntryAdmin(admin.ModelAdmin):
    list_display = ('docket', 'date_filed', 'document_number', 'description_short')
    list_filter = ('date_filed', 'docket__court')
    search_fields = ('description', 'document_number', 'docket__case_name', 'docket__docket_number')
    autocomplete_fields = ('docket', 'document')
    
    fieldsets = (
        (None, {
            'fields': ('docket', 'date_filed', 'date_entered')
        }),
        (_('Document Information'), {
            'fields': ('document_number', 'pacer_doc_id', 'pacer_seq_no', 'description')
        }),
        (_('Document Link'), {
            'fields': ('document',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + ('...' if len(obj.description) > 50 else '')
    description_short.short_description = "Description"
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)