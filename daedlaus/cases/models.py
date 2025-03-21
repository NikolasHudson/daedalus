from django.db import models
from django.conf import settings
from django.urls import reverse
import uuid
from clients.models import Client

class CaseCategory(models.Model):
    """Categories for organizing cases by practice area"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    color = models.CharField(max_length=20, blank=True, help_text="Color code for UI display")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for UI display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Case Category"
        verbose_name_plural = "Case Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Case(models.Model):
    """Main case model for legal matters"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    )
    
    # Basic information
    title = models.CharField(max_length=255)
    case_number = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(
        CaseCategory, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='cases'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    description = models.TextField(blank=True)
    
    # Unique identifier
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # Client information (foreign key to Client model)
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,  # Protect ensures cases can't be deleted by accident
        related_name='cases',
        null=True  # Allow null only for data migration
    )
    
    # Keep old fields for migration purposes, will be removed later
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=20, blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    filed_date = models.DateField(null=True, blank=True)
    
    # Team assignments
    assigned_attorneys = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='assigned_cases',
        blank=True
    )
    
    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_cases'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_cases'
    )
    
    # Portal functionality (foundation for Co-Counsel Portal)
    is_portal_enabled = models.BooleanField(
        default=False,
        help_text="Enable sharing through Co-Counsel Portal"
    )
    portal_title = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Custom title for portal display (defaults to case title)"
    )
    portal_description = models.TextField(
        blank=True,
        help_text="Custom description for portal display"
    )
    
    class Meta:
        verbose_name = "Case"
        verbose_name_plural = "Cases"
        ordering = ['-updated_at']
        permissions = [
            ("view_portal_case", "Can view case in portal"),
            ("share_case", "Can share case with external counsel"),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.case_number})"
    
    def get_absolute_url(self):
        return reverse('cases:case_detail', args=[self.uuid])
    
    def save(self, *args, **kwargs):
        # Set portal title to case title if not provided
        if not self.portal_title and self.title:
            self.portal_title = self.title
        super().save(*args, **kwargs)

class Matter(models.Model):
    """
    Sub-components for organizing complex cases
    Matters allow for dividing a case into distinct workstreams
    """
    name = models.CharField(max_length=255)
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='matters'
    )
    description = models.TextField(blank=True)
    
    # Status and tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_matters'
    )
    
    class Meta:
        verbose_name = "Matter"
        verbose_name_plural = "Matters"
        ordering = ['name']
        unique_together = [['case', 'name']]
    
    def __str__(self):
        return f"{self.name} - {self.case.title}"

class CaseFolder(models.Model):
    """
    Hierarchical folder structure for organizing documents within cases
    """
    name = models.CharField(max_length=255)
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='folders'
    )
    matter = models.ForeignKey(
        Matter,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='folders'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_folders'
    )
    
    class Meta:
        verbose_name = "Case Folder"
        verbose_name_plural = "Case Folders"
        unique_together = [['case', 'parent', 'name']]
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent}/{self.name}"
        return self.name
    
    @property
    def full_path(self):
        """Return the full path of this folder"""
        if not self.parent:
            return self.name
        return f"{self.parent.full_path}/{self.name}"

class CaseDocument(models.Model):
    """
    Association between documents and cases/folders
    This allows documents to be organized within the case folder structure
    """
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='case_associations'
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    folder = models.ForeignKey(
        CaseFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    matter = models.ForeignKey(
        Matter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    
    class Meta:
        verbose_name = "Case Document"
        verbose_name_plural = "Case Documents"
        unique_together = [['document', 'case']]
    
    def __str__(self):
        return f"{self.document} in {self.case}"