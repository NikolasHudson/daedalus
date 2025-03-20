import logging
import mimetypes
import os
from django.conf import settings
from aws.utils import get_aws_session, get_active_s3_config, BOTO3_AVAILABLE

logger = logging.getLogger(__name__)

class DocumentStorageService:
    """
    Service for handling document storage, with S3 integration when available.
    Falls back to local storage when S3 is not configured.
    """
    
    def __init__(self):
        """Initialize the document storage service."""
        self.s3_client = None
        self.s3_config = None
        self.using_s3 = False
        
        # Check if we should use S3
        if BOTO3_AVAILABLE:
            # Get active S3 media configuration
            media_config, _ = get_active_s3_config()
            
            if media_config:
                try:
                    # Create S3 client
                    session = get_aws_session(media_config)
                    self.s3_client = session.client('s3')
                    self.s3_config = media_config
                    self.using_s3 = True
                    logger.info(f"Using S3 bucket '{media_config.bucket_name}' for document storage")
                except Exception as e:
                    logger.error(f"Error initializing S3 for document storage: {str(e)}")
        
        if not self.using_s3:
            logger.info("Using local storage for documents (S3 not configured)")
    
    def upload_document(self, file_obj, document_version):
        """
        Upload a document file to storage (S3 or local).
        
        Args:
            file_obj: File object to upload
            document_version: DocumentVersion instance to associate with
            
        Returns:
            tuple: (success, message or file path)
        """
        try:
            if self.using_s3:
                return self._upload_to_s3(file_obj, document_version)
            else:
                return self._upload_to_local(file_obj, document_version)
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return False, str(e)
    
    def _upload_to_s3(self, file_obj, document_version):
        """
        Upload file to S3 bucket.
        
        Args:
            file_obj: File object to upload
            document_version: DocumentVersion instance
            
        Returns:
            tuple: (success, S3 key or error message)
        """
        # Generate S3 key based on document
        doc = document_version.document
        s3_key = f"documents/{doc.uuid}/{document_version.version_number}/{document_version.file_name}"
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(document_version.file_name)
        
        # Set extra args for upload
        extra_args = {
            'ContentType': content_type or 'application/octet-stream',
            'ServerSideEncryption': 'AES256',  # Enable encryption
        }
        
        # If file is private, add private ACL
        if doc.is_private:
            extra_args['ACL'] = 'private'
        
        try:
            # Upload to S3
            self.s3_client.upload_fileobj(
                file_obj,
                self.s3_config.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Store S3 key in document version
            document_version.s3_key = s3_key
            document_version.save(update_fields=['s3_key'])
            
            logger.info(f"Uploaded document to S3: {s3_key}")
            return True, s3_key
            
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            return False, f"Failed to upload to S3: {str(e)}"
    
    def _upload_to_local(self, file_obj, document_version):
        """
        Save file to local storage.
        
        Args:
            file_obj: File object to upload
            document_version: DocumentVersion instance
            
        Returns:
            tuple: (success, file path or error message)
        """
        try:
            # Save the file to Django's default storage
            filename = f"{document_version.document.uuid}_{document_version.version_number}_{document_version.file_name}"
            path = f"documents/{filename}"
            
            # Use Django's default storage
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            
            # Save the file
            saved_path = default_storage.save(path, ContentFile(file_obj.read()))
            
            logger.info(f"Uploaded document to local storage: {saved_path}")
            return True, saved_path
            
        except Exception as e:
            logger.error(f"Local storage error: {str(e)}")
            return False, f"Failed to save to local storage: {str(e)}"
    
    def get_document_url(self, document_version, expires=3600):
        """
        Get a URL for accessing the document.
        
        Args:
            document_version: DocumentVersion instance
            expires: URL expiration time in seconds (for S3 presigned URLs)
            
        Returns:
            tuple: (success, URL or error message)
        """
        try:
            if self.using_s3 and document_version.s3_key:
                # Generate presigned URL for S3 object
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.s3_config.bucket_name,
                        'Key': document_version.s3_key
                    },
                    ExpiresIn=expires
                )
                return True, url
            else:
                # For local storage, use media URL
                if document_version.file:
                    url = document_version.file.url
                    return True, url
                else:
                    return False, "Document file not found"
                    
        except Exception as e:
            logger.error(f"Error generating document URL: {str(e)}")
            return False, f"Failed to generate document URL: {str(e)}"
    
    def delete_document(self, document_version):
        """
        Delete a document from storage.
        
        Args:
            document_version: DocumentVersion instance
            
        Returns:
            tuple: (success, message)
        """
        try:
            if self.using_s3 and document_version.s3_key:
                # Delete from S3
                self.s3_client.delete_object(
                    Bucket=self.s3_config.bucket_name,
                    Key=document_version.s3_key
                )
                logger.info(f"Deleted document from S3: {document_version.s3_key}")
                return True, "Document deleted from S3"
            else:
                # Delete from local storage
                if document_version.file:
                    try:
                        document_version.file.delete(save=False)
                        logger.info(f"Deleted document from local storage: {document_version.file.name}")
                        return True, "Document deleted from local storage"
                    except Exception as e:
                        logger.error(f"Error deleting local file: {str(e)}")
                        return False, f"Failed to delete local file: {str(e)}"
                return False, "No file to delete"
                    
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False, f"Failed to delete document: {str(e)}"