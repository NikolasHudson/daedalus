import logging
from django.conf import settings

from ..utils import get_aws_session, get_active_s3_config, BOTO3_AVAILABLE

# Try to import boto3 dependencies, but handle gracefully if not available
if BOTO3_AVAILABLE:
    import boto3
    from botocore.exceptions import ClientError
else:
    # Create a dummy ClientError class if boto3 is not available
    class ClientError(Exception):
        pass

logger = logging.getLogger(__name__)

class S3Service:
    """
    Service class for AWS S3 operations.
    """
    def __init__(self, config=None):
        """
        Initialize the S3 service with the given configuration.
        If no configuration is provided, use the active configuration.
        
        Args:
            config: S3Configuration instance (optional)
        """
        if not BOTO3_AVAILABLE:
            logger.error("boto3 is not installed. S3 functionality will not work.")
            self.session = None
            self.client = None
            self.resource = None
            self.bucket_name = None
            self.config = None
            return
            
        if config is None:
            media_config, static_config = get_active_s3_config()
            # Use media config as default if available, otherwise static config
            self.config = media_config or static_config
        else:
            self.config = config
            
        if self.config:
            try:
                self.session = get_aws_session(self.config)
                self.client = self.session.client('s3')
                self.resource = self.session.resource('s3')
                self.bucket_name = self.config.bucket_name
            except Exception as e:
                logger.error(f"Error initializing S3 service: {str(e)}")
                self.session = None
                self.client = None
                self.resource = None
                self.bucket_name = None
        else:
            self.session = None
            self.client = None
            self.resource = None
            self.bucket_name = None
            logger.warning("No S3 configuration provided or available")
    
    def upload_file(self, file_path, object_name=None, acl='private', extra_args=None):
        """
        Upload a file to S3 bucket.
        
        Args:
            file_path: Local file path to upload
            object_name: S3 object name (if None, use file_path basename)
            acl: ACL to apply ('private', 'public-read', etc.)
            extra_args: Additional arguments to pass to upload_file
            
        Returns:
            tuple: (success, url or error message)
        """
        if not self.client:
            return False, "No S3 client available - check configuration"
        
        import os
        # If object_name not provided, use file basename
        if object_name is None:
            object_name = os.path.basename(file_path)
            
        # Prepare extra args with ACL
        if extra_args is None:
            extra_args = {'ACL': acl}
        elif 'ACL' not in extra_args:
            extra_args['ACL'] = acl
        
        try:
            self.client.upload_file(
                file_path, self.bucket_name, object_name, ExtraArgs=extra_args
            )
            
            # Generate the URL for the uploaded file
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{object_name}"
            if self.config.custom_domain:
                url = f"https://{self.config.custom_domain}/{object_name}"
                
            return True, url
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return False, str(e)
    
    def download_file(self, object_name, file_path):
        """
        Download a file from S3 bucket.
        
        Args:
            object_name: S3 object name to download
            file_path: Local file path to save to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.download_file(self.bucket_name, object_name, file_path)
            return True
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            return False
    
    def list_objects(self, prefix='', max_keys=1000):
        """
        List objects in the S3 bucket with the given prefix.
        
        Args:
            prefix: Key prefix to filter objects
            max_keys: Maximum number of keys to return
            
        Returns:
            list: List of object metadata dictionaries
        """
        if not self.client:
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                return response['Contents']
            return []
        except ClientError as e:
            logger.error(f"Error listing objects in S3: {str(e)}")
            return []
    
    def delete_object(self, object_name):
        """
        Delete an object from the S3 bucket.
        
        Args:
            object_name: Key of the object to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting object from S3: {str(e)}")
            return False
    
    def get_object_url(self, object_name, expiration=3600):
        """
        Generate a presigned URL for an object.
        
        Args:
            object_name: Key of the object
            expiration: URL expiration time in seconds
            
        Returns:
            str or None: Presigned URL or None if failed
        """
        if not self.client:
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None