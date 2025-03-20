from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
import uuid
import os
from datetime import datetime

class DocumentCategory(models.Model):
    """
    Categories for organizing documents
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Document Category")
        verbose_name_plural = _("Document Categories")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('documents:category_detail', args=[self.pk])


class Document(models.Model):
    """
    Main document model for storing files with metadata
    """
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('archived', _('Archived')),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        DocumentCategory, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    tags = models.CharField(
        max_length=255, 
        blank=True,
        help_text=_("Comma-separated tags")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Unique identifier for this document")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_documents'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_private = models.BooleanField(
        default=True,
        help_text=_("If True, only users with explicit permissions can access this document")
    )
    
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-updated_at']
        permissions = [
            ("download_document", "Can download document"),
            ("share_document", "Can share document with others"),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('documents:document_detail', args=[self.uuid])
    
    def get_tag_list(self):
        """Return tags as a list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]
    
    @property
    def current_version(self):
        """Get the most recent version of this document"""
        return self.versions.order_by('-version_number').first()
    
    @property
    def file_extension(self):
        """Get the file extension of the current version"""
        if not self.current_version:
            return None
        _, ext = os.path.splitext(self.current_version.file_name)
        return ext.lower() if ext else None


def document_file_path(instance, filename):
    """
    Generate a unique path for storing document files
    Pattern: documents/{year}/{month}/{uuid}/{filename}
    """
    now = datetime.now()
    return f'documents/{now.year}/{now.month}/{instance.document.uuid}/{filename}'


class DocumentVersion(models.Model):
    """
    Represents a specific version of a document file
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.PositiveIntegerField()
    file = models.FileField(
        upload_to=document_file_path,
        max_length=255
    )
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(
        help_text=_("File size in bytes")
    )
    file_type = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("MIME type of the file")
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        help_text=_("Notes about changes in this version")
    )
    s3_key = models.CharField(
        max_length=512,
        blank=True,
        help_text=_("S3 object key if stored in S3")
    )
    
    class Meta:
        verbose_name = _("Document Version")
        verbose_name_plural = _("Document Versions")
        ordering = ['-version_number']
        unique_together = [['document', 'version_number']]
    
    def __str__(self):
        return f"{self.document.title} v{self.version_number}"
    
    def save(self, *args, **kwargs):
        """Override save to set file metadata and handle versioning"""
        # If this is a new record, set the version number
        if not self.pk and not self.version_number:
            # Get the latest version number for this document
            latest = DocumentVersion.objects.filter(
                document=self.document
            ).order_by('-version_number').first()
            
            self.version_number = 1 if not latest else latest.version_number + 1
            
        # If file was uploaded, set metadata
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
            self.file_name = os.path.basename(self.file.name)
            
        super().save(*args, **kwargs)


class DocumentComment(models.Model):
    """
    Comments on documents
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Document Comment")
        verbose_name_plural = _("Document Comments")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.document.title}"


class DocumentAccess(models.Model):
    """
    Track document access permissions and history
    """
    ACCESS_TYPES = (
        ('view', _('View Only')),
        ('edit', _('Edit')),
        ('full', _('Full Access')),
    )
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='access_permissions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_permissions'
    )
    access_type = models.CharField(
        max_length=10,
        choices=ACCESS_TYPES,
        default='view'
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When this access expires (if temporary)")
    )
    
    class Meta:
        verbose_name = _("Document Access")
        verbose_name_plural = _("Document Access")
        unique_together = [['document', 'user']]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_access_type_display()} - {self.document.title}"