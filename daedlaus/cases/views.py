from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.contrib import messages
from django.utils.translation import gettext as _

from .models import Case, CaseCategory, Matter, CaseFolder, CaseDocument
from documents.models import Document

@login_required
def case_list(request):
    """List all cases the user has access to"""
    # Filter by category if requested
    category_id = request.GET.get('category')
    if category_id:
        try:
            category = CaseCategory.objects.get(id=category_id)
            cases = Case.objects.filter(category=category)
            title = f"Cases in {category.name}"
        except CaseCategory.DoesNotExist:
            cases = Case.objects.all()
            title = "All Cases"
    else:
        cases = Case.objects.all()
        title = "All Cases"
    
    # Get all categories for filter dropdown
    categories = CaseCategory.objects.all().order_by('name')
    
    return render(request, 'cases/case_list.html', {
        'cases': cases,
        'title': title,
        'categories': categories,
        'selected_category': category_id
    })

@login_required
def case_detail(request, uuid):
    """Display case details"""
    case = get_object_or_404(Case, uuid=uuid)
    
    # Get matters
    matters = case.matters.all()
    
    # Get root folders
    root_folders = case.folders.filter(parent=None)
    
    # Get documents directly in case root
    root_documents = case.documents.filter(folder=None)
    
    return render(request, 'cases/case_detail.html', {
        'case': case,
        'matters': matters,
        'root_folders': root_folders,
        'root_documents': root_documents,
    })

@login_required
@permission_required('cases.add_case', raise_exception=True)
def case_create(request):
    """Create a new case"""
    # Implementation will follow in next phase
    pass

@login_required
@permission_required('cases.change_case', raise_exception=True)
def case_edit(request, uuid):
    """Edit existing case"""
    # Implementation will follow in next phase
    pass

@login_required
def folder_list(request, uuid):
    """List folders for a case"""
    case = get_object_or_404(Case, uuid=uuid)
    folders = case.folders.all()
    
    return render(request, 'cases/folder_list.html', {
        'case': case,
        'folders': folders,
    })

@login_required
@permission_required('cases.add_casefolder', raise_exception=True)
def folder_create(request, uuid):
    """Create a new folder in a case"""
    # Implementation will follow in next phase
    pass

@login_required
def case_documents(request, uuid):
    """List documents for a case"""
    case = get_object_or_404(Case, uuid=uuid)
    
    # Get all associated documents
    case_docs = case.documents.all()
    
    return render(request, 'cases/case_documents.html', {
        'case': case,
        'case_documents': case_docs,
    })

@login_required
@permission_required('cases.add_casedocument', raise_exception=True)
def add_document(request, uuid):
    """Add an existing document to a case"""
    # Implementation will follow in next phase
    pass