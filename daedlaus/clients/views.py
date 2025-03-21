from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.contrib import messages
from django.utils.translation import gettext as _

from .models import Client, ClientCategory, ClientContact, ClientDocument

@login_required
def client_list(request):
    """List all clients the user has access to"""
    # Filter by category if requested
    category_id = request.GET.get('category')
    client_type = request.GET.get('type')
    
    # Start with all clients
    clients = Client.objects.all()
    
    # Apply filters
    if category_id:
        try:
            category = ClientCategory.objects.get(id=category_id)
            clients = clients.filter(category=category)
            title = f"Clients in {category.name}"
        except ClientCategory.DoesNotExist:
            title = "All Clients"
    else:
        title = "All Clients"
    
    if client_type in ['individual', 'organization']:
        clients = clients.filter(client_type=client_type)
        type_display = "Individuals" if client_type == 'individual' else "Organizations"
        title = f"{type_display}" if title == "All Clients" else f"{type_display} in {category.name}"
    
    # Get all categories for filter dropdown
    categories = ClientCategory.objects.all().order_by('name')
    
    return render(request, 'clients/client_list.html', {
        'clients': clients,
        'title': title,
        'categories': categories,
        'selected_category': category_id,
        'selected_type': client_type
    })

@login_required
def client_detail(request, uuid):
    """Display client details"""
    client = get_object_or_404(Client, uuid=uuid)
    
    # Check for confidential access
    if client.is_confidential and not request.user.has_perm('clients.view_confidential_client'):
        messages.error(request, _("You don't have permission to view this confidential client."))
        return redirect('clients:client_list')
    
    # Get contacts if organization
    contacts = []
    if client.is_organization:
        contacts = client.contacts.all().order_by('-is_primary', 'name')
    
    # Get associated cases
    cases = client.cases.all().order_by('-created_at')
    
    # Get client documents
    documents = client.documents.all().order_by('-added_at')
    
    return render(request, 'clients/client_detail.html', {
        'client': client,
        'contacts': contacts,
        'cases': cases,
        'documents': documents,
    })

@login_required
@permission_required('clients.add_client', raise_exception=True)
def client_create(request):
    """Create a new client"""
    # Implementation will follow in next phase
    pass

@login_required
@permission_required('clients.change_client', raise_exception=True)
def client_edit(request, uuid):
    """Edit existing client"""
    # Implementation will follow in next phase
    pass

@login_required
def client_documents(request, uuid):
    """List documents for a client"""
    client = get_object_or_404(Client, uuid=uuid)
    
    # Check for confidential access
    if client.is_confidential and not request.user.has_perm('clients.view_confidential_client'):
        messages.error(request, _("You don't have permission to view this confidential client."))
        return redirect('clients:client_list')
    
    # Get all associated documents
    client_docs = client.documents.all().order_by('-added_at')
    
    return render(request, 'clients/client_documents.html', {
        'client': client,
        'client_documents': client_docs,
    })

@login_required
@permission_required('clients.add_clientdocument', raise_exception=True)
def add_document(request, uuid):
    """Add an existing document to a client"""
    # Implementation will follow in next phase
    pass

@login_required
def client_cases(request, uuid):
    """List cases for a client"""
    client = get_object_or_404(Client, uuid=uuid)
    
    # Check for confidential access
    if client.is_confidential and not request.user.has_perm('clients.view_confidential_client'):
        messages.error(request, _("You don't have permission to view this confidential client."))
        return redirect('clients:client_list')
    
    # Get all associated cases
    cases = client.cases.all().order_by('-created_at')
    
    return render(request, 'clients/client_cases.html', {
        'client': client,
        'cases': cases,
    })

@login_required
@permission_required('clients.add_clientcontact', raise_exception=True)
def add_contact(request, uuid):
    """Add a contact to an organization client"""
    # Implementation will follow in next phase
    pass

@login_required
@permission_required('clients.change_clientcontact', raise_exception=True)
def edit_contact(request, uuid, contact_id):
    """Edit a contact for an organization client"""
    # Implementation will follow in next phase
    pass