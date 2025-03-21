from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db import transaction

from .models import Court, Docket, Party, Attorney, DocketEntry
from cases.models import Case

@login_required
def court_list(request):
    """List all courts"""
    level = request.GET.get('level')
    state = request.GET.get('state')
    
    courts = Court.objects.all()
    
    if level:
        courts = courts.filter(level=level)
    if state:
        courts = courts.filter(state=state)
    
    # Get unique states for filter
    states = Court.objects.values_list('state', flat=True).distinct().order_by('state')
    
    return render(request, 'docket/court_list.html', {
        'courts': courts,
        'states': states,
        'level': level,
        'state': state
    })

@login_required
def court_detail(request, court_id):
    """Show details for a specific court"""
    court = get_object_or_404(Court, id=court_id)
    dockets = court.dockets.all()[:20]  # Limit to 20 most recent
    
    return render(request, 'docket/court_detail.html', {
        'court': court,
        'dockets': dockets,
    })

@login_required
def docket_list(request):
    """List all dockets"""
    court_id = request.GET.get('court')
    active_only = request.GET.get('active') == 'true'
    
    dockets = Docket.objects.all()
    
    if court_id:
        dockets = dockets.filter(court_id=court_id)
    if active_only:
        dockets = dockets.filter(date_terminated__isnull=True)
    
    # Get all courts for filter
    courts = Court.objects.all().order_by('name')
    
    return render(request, 'docket/docket_list.html', {
        'dockets': dockets,
        'courts': courts,
        'selected_court': court_id,
        'active_only': active_only
    })

@login_required
def docket_detail(request, docket_id):
    """Show details for a specific docket"""
    docket = get_object_or_404(Docket, id=docket_id)
    parties = docket.parties.all()
    entries = docket.entries.all()[:50]  # Limit to 50 most recent
    
    return render(request, 'docket/docket_detail.html', {
        'docket': docket,
        'parties': parties,
        'entries': entries,
    })

@login_required
def docket_entries(request, docket_id):
    """Show all entries for a docket with pagination"""
    docket = get_object_or_404(Docket, id=docket_id)
    entries = docket.entries.all()
    
    return render(request, 'docket/docket_entries.html', {
        'docket': docket,
        'entries': entries,
    })

@login_required
def case_docket(request, case_uuid):
    """Show docket for a specific case"""
    case = get_object_or_404(Case, uuid=case_uuid)
    try:
        docket = case.docket
        return redirect('docket:docket_detail', docket_id=docket.id)
    except Docket.DoesNotExist:
        return render(request, 'docket/case_no_docket.html', {
            'case': case,
        })

@login_required
@permission_required('docket.add_docket', raise_exception=True)
def create_case_docket(request, case_uuid):
    """Create a new docket for a case"""
    # Implementation will follow in next phase
    pass

@login_required
@permission_required('docket.add_docketentry', raise_exception=True)
def add_docket_entry(request, docket_id):
    """Add a new entry to a docket"""
    # Implementation will follow in next phase
    pass

@login_required
@permission_required('docket.add_party', raise_exception=True)
def add_party(request, docket_id):
    """Add a new party to a docket"""
    # Implementation will follow in next phase
    pass

@login_required
@permission_required('docket.add_attorney', raise_exception=True)
def add_attorney(request, party_id):
    """Add a new attorney to a party"""
    # Implementation will follow in next phase
    pass