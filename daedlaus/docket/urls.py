from django.urls import path
from . import views

app_name = 'docket'

urlpatterns = [
    path('courts/', views.court_list, name='court_list'),
    path('courts/<int:court_id>/', views.court_detail, name='court_detail'),
    path('dockets/', views.docket_list, name='docket_list'),
    path('dockets/<int:docket_id>/', views.docket_detail, name='docket_detail'),
    path('dockets/<int:docket_id>/entries/', views.docket_entries, name='docket_entries'),
    path('cases/<uuid:case_uuid>/docket/', views.case_docket, name='case_docket'),
    path('cases/<uuid:case_uuid>/docket/create/', views.create_case_docket, name='create_case_docket'),
    path('dockets/<int:docket_id>/add-entry/', views.add_docket_entry, name='add_docket_entry'),
    path('dockets/<int:docket_id>/add-party/', views.add_party, name='add_party'),
    path('parties/<int:party_id>/add-attorney/', views.add_attorney, name='add_attorney'),
]