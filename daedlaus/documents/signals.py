import logging
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from .models import DocumentVersion
from .services.s3_service import DocumentStorageService

logger = logging.getLogger(__name__)

# Initialize the document storage service
document_service = DocumentStorageService()

@receiver(post_save, sender=DocumentVersion)
def handle_document_version_upload(sender, instance, created, **kwargs):
    """
    Signal handler to upload document version to S3 if it's configured
    """
    # Only process if we're using S3 and there's a file to upload
    if document_service.using_s3 and instance.file and not instance.s3_key:
        try:
            # Reopen the file for reading
            instance.file.open('rb')
            
            # Upload to S3
            success, result = document_service.upload_document(instance.file, instance)
            
            # Log the result
            if success:
                logger.info(f"Document uploaded to S3: {result}")
            else:
                logger.error(f"Failed to upload document to S3: {result}")
                
            # Make sure to close the file
            instance.file.close()
            
        except Exception as e:
            logger.exception(f"Error handling document upload: {str(e)}")


@receiver(pre_delete, sender=DocumentVersion)
def handle_document_version_delete(sender, instance, **kwargs):
    """
    Signal handler to delete document version from S3 if it's there
    """
    if document_service.using_s3 and instance.s3_key:
        try:
            # Delete from S3
            success, result = document_service.delete_document(instance)
            
            # Log the result
            if success:
                logger.info(f"Document deleted from S3: {instance.s3_key}")
            else:
                logger.error(f"Failed to delete document from S3: {result}")
                
        except Exception as e:
            logger.exception(f"Error handling document deletion: {str(e)}")