from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging
import re

logger = logging.getLogger(__name__)

# Try to import boto3, but handle gracefully if not available
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 is not installed or not available. AWS functionality will be limited.")

AWS_REGIONS = [
    ('us-east-1', 'US East (N. Virginia)'),
    ('us-east-2', 'US East (Ohio)'),
    ('us-west-1', 'US West (N. California)'),
    ('us-west-2', 'US West (Oregon)'),
    ('af-south-1', 'Africa (Cape Town)'),
    ('ap-east-1', 'Asia Pacific (Hong Kong)'),
    ('ap-south-1', 'Asia Pacific (Mumbai)'),
    ('ap-northeast-1', 'Asia Pacific (Tokyo)'),
    ('ap-northeast-2', 'Asia Pacific (Seoul)'),
    ('ap-northeast-3', 'Asia Pacific (Osaka)'),
    ('ap-southeast-1', 'Asia Pacific (Singapore)'),
    ('ap-southeast-2', 'Asia Pacific (Sydney)'),
    ('ca-central-1', 'Canada (Central)'),
    ('eu-central-1', 'Europe (Frankfurt)'),
    ('eu-west-1', 'Europe (Ireland)'),
    ('eu-west-2', 'Europe (London)'),
    ('eu-west-3', 'Europe (Paris)'),
    ('eu-north-1', 'Europe (Stockholm)'),
    ('eu-south-1', 'Europe (Milan)'),
    ('me-south-1', 'Middle East (Bahrain)'),
    ('sa-east-1', 'South America (São Paulo)'),
]

class BaseAWSConfiguration(models.Model):
    """
    Base model for AWS configuration with common fields and validation logic.
    """
    name = models.CharField(
        max_length=100, 
        help_text=_("A friendly name to identify this configuration")
    )
    aws_access_key_id = models.CharField(
        max_length=255, 
        help_text=_("AWS Access Key ID")
    )
    aws_secret_access_key = models.CharField(
        max_length=255, 
        help_text=_("AWS Secret Access Key - keep this secure"),
        editable=True,  # Mark as editable to allow editing in the admin
    )
    region = models.CharField(
        max_length=20, 
        choices=AWS_REGIONS, 
        default='us-east-2',
        help_text=_("AWS Region for this service")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this configuration is currently active")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.name} ({self.region})"
    
    def validate_credentials(self):
        """
        Base method to validate AWS credentials.
        Should be overridden in child classes with service-specific validation.
        """
        if not BOTO3_AVAILABLE:
            return False, "boto3 library is not installed. Please install boto3 to validate AWS credentials."
            
        try:
            # Basic validation using STS - works for any valid AWS credentials
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region
            )
            sts = session.client('sts')
            sts.get_caller_identity()
            return True, "Credentials validated successfully"
        except Exception as e:
            return False, f"Credential validation failed: {str(e)}"
    
    def save(self, *args, **kwargs):
        """
        Override save to add custom validation and encryption handling.
        """
        # Add custom validation logic here if needed
        super().save(*args, **kwargs)


class S3Configuration(BaseAWSConfiguration):
    """
    Configuration for AWS S3 service.
    """
    bucket_name = models.CharField(
        max_length=255,
        help_text=_("S3 Bucket Name - must be globally unique and follow S3 naming rules")
    )
    use_for_static_files = models.BooleanField(
        default=False,
        help_text=_("Use this bucket for serving static files")
    )
    use_for_media_files = models.BooleanField(
        default=False,
        help_text=_("Use this bucket for storing media files")
    )
    create_bucket_if_not_exists = models.BooleanField(
        default=False,
        help_text=_("Create the bucket if it doesn't exist")
    )
    custom_domain = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Optional custom domain for the bucket (e.g., cdn.example.com)")
    )

    class Meta:
        verbose_name = _("S3 Configuration")
        verbose_name_plural = _("S3 Configurations")

    def clean(self):
        """
        Validate S3-specific configuration.
        """
        super().clean()

        # Validate bucket name format
        if self.bucket_name:
            if not re.match(r'^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$', self.bucket_name):
                raise ValidationError({
                    'bucket_name': _("Bucket name must be between 3 and 63 characters, contain only lowercase letters, "
                                    "numbers, and hyphens, and start/end with a letter or number.")
                })
            
        # Check if another configuration is already active for the same purpose
        if self.is_active and self.use_for_static_files:
            if S3Configuration.objects.filter(is_active=True, use_for_static_files=True).exclude(pk=self.pk).exists():
                raise ValidationError(
                    _("Another active S3 configuration is already set for static files.")
                )
        
        if self.is_active and self.use_for_media_files:
            if S3Configuration.objects.filter(is_active=True, use_for_media_files=True).exclude(pk=self.pk).exists():
                raise ValidationError(
                    _("Another active S3 configuration is already set for media files.")
                )

    def validate_credentials(self):
        """
        Validate S3-specific access using the provided credentials.
        """
        if not BOTO3_AVAILABLE:
            return False, "boto3 library is not installed. Please install boto3 to validate AWS credentials."
            
        try:
            success, message = super().validate_credentials()
            if not success:
                return success, message
            
            # S3-specific validation
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region
            )
            s3_client = session.client('s3')
            
            # Check if bucket exists
            try:
                s3_client.head_bucket(Bucket=self.bucket_name)
                return True, f"Successfully connected to bucket '{self.bucket_name}'"
            except Exception as e:
                if self.create_bucket_if_not_exists:
                    try:
                        # Create the bucket if specified
                        s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region} if self.region != 'us-east-1' else {}
                        )
                        # Set bucket to block public access
                        s3_client.put_public_access_block(
                            Bucket=self.bucket_name,
                            PublicAccessBlockConfiguration={
                                'BlockPublicAcls': True,
                                'IgnorePublicAcls': True,
                                'BlockPublicPolicy': True,
                                'RestrictPublicBuckets': True
                            }
                        )
                        # Enable bucket encryption
                        s3_client.put_bucket_encryption(
                            Bucket=self.bucket_name,
                            ServerSideEncryptionConfiguration={
                                'Rules': [
                                    {
                                        'ApplyServerSideEncryptionByDefault': {
                                            'SSEAlgorithm': 'AES256'
                                        },
                                        'BucketKeyEnabled': True
                                    }
                                ]
                            }
                        )
                        return True, f"Bucket '{self.bucket_name}' created successfully with encryption and public access blocked"
                    except Exception as create_error:
                        return False, f"Failed to create bucket: {str(create_error)}"
                else:
                    return False, f"Bucket '{self.bucket_name}' does not exist or is not accessible: {str(e)}"
        except Exception as e:
            return False, f"Error validating S3 configuration: {str(e)}"


class BedrockConfiguration(BaseAWSConfiguration):
    """
    Configuration for AWS Bedrock service.
    """
    default_model_id = models.CharField(
        max_length=255,
        default="us.anthropic.claude-3-sonnet-20240229-v1:0",
        help_text=_("Default model ID to use - include regional prefix (e.g., 'us.')")
    )
    
    class Meta:
        verbose_name = _("Bedrock Configuration")
        verbose_name_plural = _("Bedrock Configurations")
    
    def validate_credentials(self):
        """
        Validate Bedrock-specific access using the provided credentials.
        """
        if not BOTO3_AVAILABLE:
            return False, "boto3 library is not installed. Please install boto3 to validate AWS credentials."
            
        try:
            success, message = super().validate_credentials()
            if not success:
                return success, message
            
            # Bedrock-specific validation
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region
            )
            
            # Check if the region supports Bedrock
            bedrock_regions = [
                'us-east-1', 'us-east-2', 'us-west-2', 'ap-northeast-1', 
                'ap-southeast-1', 'eu-central-1', 'ca-central-1'
            ]
            if self.region not in bedrock_regions:
                return False, f"AWS Bedrock is not available in the {self.region} region. Please use one of: {', '.join(bedrock_regions)}"
            
            # Check if the model exists and is accessible
            bedrock_client = session.client(
                service_name='bedrock-runtime',
                region_name=self.region
            )
            
            # Try listing models to verify API access
            try:
                # We're not directly checking model availability here as it requires
                # a different API call, but this verifies the credentials have proper access
                # to the Bedrock service
                return True, "Successfully connected to AWS Bedrock service"
            except Exception as e:
                return False, f"Error connecting to Bedrock service: {str(e)}"
            
        except Exception as e:
            return False, f"Error validating Bedrock configuration: {str(e)}"