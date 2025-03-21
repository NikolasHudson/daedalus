from django.db import models
from django.conf import settings
from django.urls import reverse
import uuid

class ClientType(models.TextChoices):
    INDIVIDUAL = 'individual', 'Individual'
    ORGANIZATION = 'organization', 'Organization'

class ClientCategory(models.Model):
    """
    Categories for classifying clients (e.g., VIP, Standard, Pro Bono)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, blank=True, help_text="Color code for UI display")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Client Category"
        verbose_name_plural = "Client Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Client(models.Model):
    """
    Main client model for both individuals and organizations
    """
    # Basic information
    name = models.CharField(max_length=255, help_text="Full name for individuals, organization name for entities")
    client_type = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.INDIVIDUAL
    )
    category = models.ForeignKey(
        ClientCategory, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients'
    )
    
    # Unique identifier
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # Contact information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Individual-specific fields
    date_of_birth = models.DateField(null=True, blank=True)
    ssn_last_four = models.CharField(max_length=4, blank=True, verbose_name="Last 4 of SSN")
    
    # Organization-specific fields
    tax_id = models.CharField(max_length=50, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    
    # Client status and classification
    is_active = models.BooleanField(default=True)
    intake_date = models.DateField(null=True, blank=True)
    referral_source = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    # Privacy and security classification
    is_confidential = models.BooleanField(
        default=False,
        help_text="Restrict access to this client to assigned attorneys only"
    )
    data_classification = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('confidential', 'Confidential'),
            ('privileged', 'Privileged')
        ],
        default='confidential'
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_clients'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_clients'
    )
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['name']
        permissions = [
            ("view_confidential_client", "Can view confidential client information"),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('clients:client_detail', args=[self.uuid])
    
    @property
    def is_individual(self):
        return self.client_type == ClientType.INDIVIDUAL
    
    @property
    def is_organization(self):
        return self.client_type == ClientType.ORGANIZATION
    
    @property
    def full_address(self):
        """Returns the full formatted address"""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.postal_code}".strip(),
            self.country
        ]
        return "\n".join(p for p in parts if p)

class ClientContact(models.Model):
    """
    Contact people for organization clients
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Designate as the primary contact for this organization"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Client Contact"
        verbose_name_plural = "Client Contacts"
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.client.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary contact per client
        if self.is_primary:
            ClientContact.objects.filter(
                client=self.client, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class ClientDocument(models.Model):
    """
    Association between documents and clients
    This allows for client-specific documents (e.g., intake forms, agreements)
    """
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='client_associations'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('engagement', 'Engagement Agreement'),
            ('id', 'Identification Document'),
            ('intake', 'Intake Form'),
            ('correspondence', 'Correspondence'),
            ('other', 'Other')
        ],
        default='other'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    
    class Meta:
        verbose_name = "Client Document"
        verbose_name_plural = "Client Documents"
        unique_together = [['document', 'client']]
    
    def __str__(self):
        return f"{self.document} for {self.client}"