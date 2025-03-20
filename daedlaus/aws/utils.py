import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import boto3, but handle gracefully if not available
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 is not installed or not available. AWS functionality will be limited.")

def get_aws_session(config):
    """
    Create a boto3 session from the given configuration object.
    
    Args:
        config: An AWS configuration object with appropriate attributes
        
    Returns:
        boto3.Session: A configured boto3 session
    """
    if not BOTO3_AVAILABLE:
        raise ImportError("boto3 is not installed. Please install boto3 to use AWS functionality.")
        
    if not hasattr(config, 'aws_access_key_id') or not hasattr(config, 'aws_secret_access_key'):
        raise ValueError("Config object must have aws_access_key_id and aws_secret_access_key attributes")
    
    return boto3.Session(
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        region_name=getattr(config, 'region', 'us-east-2')
    )

def get_active_s3_config():
    """
    Get the active S3 configuration for media or static files.
    
    Returns:
        tuple: (media_config, static_config) - may be None if not configured
    """
    from .models import S3Configuration
    
    try:
        # Get active configs for media and static files
        media_config = S3Configuration.objects.filter(
            is_active=True, use_for_media_files=True
        ).first()
        
        static_config = S3Configuration.objects.filter(
            is_active=True, use_for_static_files=True
        ).first()
        
        return media_config, static_config
    except Exception as e:
        logger.error(f"Error retrieving active S3 configurations: {str(e)}")
        return None, None

def get_active_bedrock_config():
    """
    Get the active Bedrock configuration.
    
    Returns:
        BedrockConfiguration or None: The active configuration or None if not found
    """
    from .models import BedrockConfiguration
    
    try:
        return BedrockConfiguration.objects.filter(is_active=True).first()
    except Exception as e:
        logger.error(f"Error retrieving active Bedrock configuration: {str(e)}")
        return None

def get_bedrock_client():
    """
    Get a configured boto3 client for Bedrock.
    
    Returns:
        boto3.client or None: Configured client or None if no active config
    """
    if not BOTO3_AVAILABLE:
        logger.error("boto3 is not installed. Cannot create Bedrock client.")
        return None
        
    config = get_active_bedrock_config()
    
    if not config:
        logger.warning("No active Bedrock configuration found")
        return None
    
    try:
        session = get_aws_session(config)
        return session.client(
            service_name='bedrock-runtime',
            region_name=config.region
        )
    except Exception as e:
        logger.error(f"Error creating Bedrock client: {str(e)}")
        return None

def update_settings_from_s3_config():
    """
    Update Django settings with S3 configurations from the database.
    Called during startup to override settings with database configurations.
    
    Returns:
        bool: True if settings were updated, False otherwise
    """
    if not BOTO3_AVAILABLE:
        logger.warning("boto3 is not installed. Cannot update S3 settings.")
        return False
        
    try:
        media_config, static_config = get_active_s3_config()
        
        if not media_config and not static_config:
            logger.info("No active S3 configurations found in database")
            return False
            
        # Update Django settings for S3
        if hasattr(settings, '_wrapped'):
            django_settings = settings._wrapped
        else:
            django_settings = settings
            
        # Use either media or static config for common settings
        config = media_config or static_config
        
        if config:
            logger.info(f"Updating Django settings with S3 configuration: {config.name}")
            
            # Common S3 settings
            django_settings.AWS_S3_ENABLED = True
            django_settings.AWS_ACCESS_KEY_ID = config.aws_access_key_id
            django_settings.AWS_SECRET_ACCESS_KEY = config.aws_secret_access_key
            django_settings.AWS_S3_REGION_NAME = config.region
            django_settings.AWS_DEFAULT_ACL = 'private'
            django_settings.AWS_S3_ENCRYPTION = True
        
        # Media-specific settings
        if media_config:
            django_settings.AWS_STORAGE_BUCKET_NAME = media_config.bucket_name
            django_settings.AWS_S3_CUSTOM_DOMAIN = media_config.custom_domain or f'{media_config.bucket_name}.s3.amazonaws.com'
            django_settings.MEDIA_LOCATION = 'media'
            django_settings.MEDIA_URL = f'https://{django_settings.AWS_S3_CUSTOM_DOMAIN}/{django_settings.MEDIA_LOCATION}/'
            django_settings.DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
            
        # Static-specific settings
        if static_config:
            if not media_config:
                # Only set these if not already set by media config
                django_settings.AWS_STORAGE_BUCKET_NAME = static_config.bucket_name
                django_settings.AWS_S3_CUSTOM_DOMAIN = static_config.custom_domain or f'{static_config.bucket_name}.s3.amazonaws.com'
                
            django_settings.AWS_LOCATION = 'static'
            django_settings.STATIC_URL = f'https://{django_settings.AWS_S3_CUSTOM_DOMAIN}/{django_settings.AWS_LOCATION}/'
            django_settings.STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
            
        return True
            
    except Exception as e:
        logger.error(f"Error updating settings from S3 config: {str(e)}")
        return False