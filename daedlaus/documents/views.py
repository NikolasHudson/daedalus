import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404, FileResponse
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db import transaction
from django.core.paginator import Paginator
from .models import Document, DocumentCategory, DocumentVersion, DocumentAccess
from .services.s3_service import DocumentStorageService
import logging

logger = logging.getLogger(__name__)
document_service = DocumentStorageService()

@login_required
def document_list(request):
    """
    Display a list of documents the user has access to
    """
    # Check if we filter by category
    category_id = request.GET.get('category')
    if category_id:
        try:
            category = DocumentCategory.objects.get(id=category_id)
            document_list = Document.objects.filter(category=category)
            title = f"Documents in {category.name}"
        except DocumentCategory.DoesNotExist:
            document_list = Document.objects.all()
            title = "All Documents"
    else:
        document_list = Document.objects.all()
        title = "All Documents"
    
    # Pagination
    paginator = Paginator(document_list, 15)  # Show 15 documents per page
    page_number = request.GET.get('page')
    documents = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = DocumentCategory.objects.all().order_by('name')
    
    return render(request, 'documents/document_list.html', {
        'documents': documents,
        'title': title,
        'categories': categories,
        'selected_category': category_id
    })

@login_required
def document_detail(request, uuid):
    """
    Display document details
    """
    document = get_object_or_404(Document, uuid=uuid)
    
    # Access control check
    if document.is_private:
        # Check if user has access
        access = DocumentAccess.objects.filter(document=document, user=request.user).first()
        if not access and not request.user.has_perm('documents.view_document'):
            messages.error(request, _("You don't have permission to view this document."))
            return redirect('documents:document_list')
    
    # Get versions, most recent first
    versions = document.versions.all().order_by('-version_number')
    
    return render(request, 'documents/document_detail.html', {
        'document': document,
        'versions': versions,
    })

@login_required
def document_download(request, uuid, version=None):
    """
    Download a specific document version
    """
    document = get_object_or_404(Document, uuid=uuid)
    
    # Access control check
    if document.is_private:
        # Check if user has access
        access = DocumentAccess.objects.filter(document=document, user=request.user).first()
        if not access and not request.user.has_perm('documents.download_document'):
            messages.error(request, _("You don't have permission to download this document."))
            return redirect('documents:document_detail', uuid=uuid)
    
    # Get requested version or default to latest
    if version:
        doc_version = get_object_or_404(DocumentVersion, document=document, version_number=version)
    else:
        doc_version = document.current_version
        if not doc_version:
            messages.error(request, _("No versions available for this document."))
            return redirect('documents:document_detail', uuid=uuid)
    
    # Check if we're using S3
    if document_service.using_s3 and doc_version.s3_key:
        # Get presigned URL
        success, url = document_service.get_document_url(doc_version)
        if success:
            # Redirect to presigned URL
            return redirect(url)
        else:
            messages.error(request, _("Error retrieving document: {0}").format(url))
            return redirect('documents:document_detail', uuid=uuid)
    
    # Fallback to local file
    if doc_version.file:
        # Try to determine content type
        content_type, encoding = mimetypes.guess_type(doc_version.file_name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        try:
            response = FileResponse(doc_version.file, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{doc_version.file_name}"'
            return response
        except Exception as e:
            logger.error(f"Error downloading document: {str(e)}")
            messages.error(request, _("Error retrieving document. Please try again later."))
            return redirect('documents:document_detail', uuid=uuid)
    
    # If we get here, no file is available
    messages.error(request, _("Document file not found."))
    return redirect('documents:document_detail', uuid=uuid)

@login_required
def document_upload(request):
    """
    Upload a new document or a new version of an existing document
    """
    # Handle form submission
    if request.method == 'POST':
        # Check if it's a new document or new version
        document_id = request.POST.get('document_id')
        
        if document_id:
            # New version for existing document
            try:
                document = Document.objects.get(pk=document_id)
                
                # Check permissions
                if not request.user.has_perm('documents.change_document'):
                    messages.error(request, _("You don't have permission to add new versions."))
                    return redirect('documents:document_list')
                
                # Process uploaded file
                if 'file' not in request.FILES:
                    messages.error(request, _("No file was uploaded."))
                    return redirect('documents:document_detail', uuid=document.uuid)
                
                file = request.FILES['file']
                notes = request.POST.get('notes', '')
                
                # Create the new version
                with transaction.atomic():
                    version = DocumentVersion(
                        document=document,
                        file=file,
                        file_name=file.name,
                        file_size=file.size,
                        notes=notes,
                        uploaded_by=request.user
                    )
                    version.save()
                
                messages.success(request, _("New version uploaded successfully."))
                return redirect('documents:document_detail', uuid=document.uuid)
                
            except Document.DoesNotExist:
                messages.error(request, _("Document not found."))
                return redirect('documents:document_list')
        else:
            # New document
            if not request.user.has_perm('documents.add_document'):
                messages.error(request, _("You don't have permission to add new documents."))
                return redirect('documents:document_list')
            
            # Process form data
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category')
            is_private = request.POST.get('is_private') == 'on'
            tags = request.POST.get('tags', '')
            
            # Validate required fields
            if not title:
                messages.error(request, _("Title is required."))
                return render(request, 'documents/document_upload.html', {
                    'categories': DocumentCategory.objects.all().order_by('name')
                })
            
            # Process uploaded file
            if 'file' not in request.FILES:
                messages.error(request, _("No file was uploaded."))
                return render(request, 'documents/document_upload.html', {
                    'categories': DocumentCategory.objects.all().order_by('name')
                })
            
            file = request.FILES['file']
            
            # Create the document and first version
            with transaction.atomic():
                # Create document
                category = None
                if category_id:
                    try:
                        category = DocumentCategory.objects.get(pk=category_id)
                    except DocumentCategory.DoesNotExist:
                        pass
                        
                document = Document(
                    title=title,
                    description=description,
                    category=category,
                    is_private=is_private,
                    tags=tags,
                    created_by=request.user,
                    updated_by=request.user
                )
                document.save()
                
                # Create initial version
                version = DocumentVersion(
                    document=document,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    uploaded_by=request.user
                )
                version.save()
            
            messages.success(request, _("Document uploaded successfully."))
            return redirect('documents:document_detail', uuid=document.uuid)
    
    # Display the upload form
    return render(request, 'documents/document_upload.html', {
        'categories': DocumentCategory.objects.all().order_by('name')
    })