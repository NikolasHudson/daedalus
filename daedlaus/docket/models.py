from django.db import models
from django.conf import settings
from django.urls import reverse
from cases.models import Case

class Court(models.Model):
    """
    Model representing a court (federal, state, or local)
    """
    COURT_LEVELS = [
        ('federal', 'Federal'),
        ('state', 'State'),
        ('local', 'Local'),
        ('administrative', 'Administrative'),
    ]
    
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=COURT_LEVELS)
    jurisdiction = models.CharField(max_length=255)
    
    # Location information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Contact information
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Electronic filing information
    e_filing_available = models.BooleanField(default=False)
    e_filing_url = models.URLField(blank=True)
    
    # System codes for integration
    pacer_code = models.CharField(max_length=20, blank=True, verbose_name="PACER Court Code")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Court"
        verbose_name_plural = "Courts"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

class Docket(models.Model):
    """
    Case docket information - can be linked to our internal Case model
    """
    # Link to our internal case
    case = models.OneToOneField(
        Case, 
        on_delete=models.CASCADE, 
        related_name='docket',
        null=True,
        blank=True
    )
    
    # Court information
    court = models.ForeignKey(
        Court,
        on_delete=models.PROTECT,
        related_name='dockets'
    )
    
    # Docket identifiers
    docket_number = models.CharField(max_length=100)
    case_name = models.CharField(max_length=255)
    
    # Dates
    date_filed = models.DateField()
    date_terminated = models.DateField(null=True, blank=True)
    date_converted = models.DateField(null=True, blank=True, help_text="Date when case was converted to another type")
    date_discharged = models.DateField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.CharField(max_length=255, blank=True, help_text="Judge or official assigned to the case")
    referred_to = models.CharField(max_length=255, blank=True, help_text="Additional referral information")
    
    # Case details
    cause = models.CharField(max_length=255, blank=True)
    nature_of_suit = models.CharField(max_length=255, blank=True)
    jury_demand = models.CharField(max_length=100, blank=True)
    demand = models.TextField(blank=True)
    jurisdiction = models.CharField(max_length=255, blank=True)
    mdl_status = models.CharField(max_length=100, blank=True, verbose_name="MDL Status")
    
    # Federal-specific fields
    federal_office_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Federal DN Office Code")
    federal_case_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Federal DN Case Type")
    federal_judge_initials_assigned = models.CharField(max_length=10, blank=True, verbose_name="Federal Judge Initials (Assigned)")
    federal_judge_initials_referred = models.CharField(max_length=10, blank=True, null=True, verbose_name="Federal Judge Initials (Referred)")
    federal_defendant_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Federal Defendant Number")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_dockets'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_dockets'
    )
    
    class Meta:
        verbose_name = "Docket"
        verbose_name_plural = "Dockets"
        ordering = ['-date_filed']
        unique_together = [['court', 'docket_number']]
    
    def __str__(self):
        return f"{self.case_name} ({self.docket_number})"
    
    def get_absolute_url(self):
        return reverse('docket:docket_detail', args=[self.id])
    
    @property
    def is_active(self):
        """Check if the case is still active (not terminated)"""
        return self.date_terminated is None

class Party(models.Model):
    """
    Party involved in a case (plaintiff, defendant, intervenor, etc.)
    """
    PARTY_TYPES = [
        ('plaintiff', 'Plaintiff'),
        ('defendant', 'Defendant'),
        ('debtor', 'Debtor'),
        ('creditor', 'Creditor'),
        ('trustee', 'Trustee'),
        ('us_trustee', 'U.S. Trustee'),
        ('third_party', 'Third Party'),
        ('intervenor', 'Intervenor'),
        ('petitioner', 'Petitioner'),
        ('respondent', 'Respondent'),
        ('claimant', 'Claimant'),
        ('appellant', 'Appellant'),
        ('appellee', 'Appellee'),
        ('interested_party', 'Interested Party'),
        ('mediator', 'Mediator'),
        ('other', 'Other'),
    ]
    
    docket = models.ForeignKey(
        Docket,
        on_delete=models.CASCADE,
        related_name='parties'
    )
    type = models.CharField(max_length=20, choices=PARTY_TYPES)
    name = models.CharField(max_length=255)
    extra_info = models.TextField(blank=True, help_text="Additional details such as address or contact information")
    date_terminated = models.DateField(null=True, blank=True)
    
    # Optional link to our internal client
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='docket_appearances'
    )
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Party"
        verbose_name_plural = "Parties"
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Attorney(models.Model):
    """
    Attorney representing a party in a case
    """
    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name='attorneys'
    )
    name = models.CharField(max_length=255)
    roles = models.CharField(max_length=255, blank=True, help_text="Comma-separated roles")
    contact = models.TextField(blank=True, help_text="Contact information including address, phone, email, etc.")
    
    # Optional link to our internal user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='docket_appearances'
    )
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Attorney"
        verbose_name_plural = "Attorneys"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} for {self.party}"
    
    def get_roles_list(self):
        """Return roles as a list"""
        if not self.roles:
            return []
        return [role.strip() for role in self.roles.split(',')]

class DocketEntry(models.Model):
    """
    Entry in a case docket (filing, order, hearing, etc.)
    """
    docket = models.ForeignKey(
        Docket,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    
    # Entry details
    date_filed = models.DateField()
    date_entered = models.DateField(help_text="Date when the entry was officially entered into the system")
    document_number = models.CharField(max_length=50, blank=True, help_text="Sequential or identifying number for the document")
    pacer_doc_id = models.CharField(max_length=100, blank=True, verbose_name="PACER Document ID")
    pacer_seq_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="PACER Sequence Number")
    description = models.TextField(help_text="Detailed description of the docket entry")
    
    # Document link (if available)
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='docket_entries'
    )
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_entries'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_entries'
    )
    
    class Meta:
        verbose_name = "Docket Entry"
        verbose_name_plural = "Docket Entries"
        ordering = ['-date_filed', '-date_entered']
    
    def __str__(self):
        doc_num = f"#{self.document_number}" if self.document_number else ""
        return f"{self.date_filed} {doc_num}: {self.description[:50]}..."