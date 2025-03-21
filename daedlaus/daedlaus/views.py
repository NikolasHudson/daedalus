from django.shortcuts import render
from django.db.models import Q
from documents.models import Document

def search_view(request):
    """
    Universal search view that searches across all modules
    """
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    
    results = {
        'documents': [],
    }
    
    if query:
        # Search documents
        if search_type in ['all', 'documents']:
            results['documents'] = Document.objects.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )[:10]
    
    return render(request, 'search_results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'active_page': 'search'
    })