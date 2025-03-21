from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('create/', views.client_create, name='client_create'),
    path('<uuid:uuid>/', views.client_detail, name='client_detail'),
    path('<uuid:uuid>/edit/', views.client_edit, name='client_edit'),
    path('<uuid:uuid>/add-contact/', views.add_contact, name='add_contact'),
    path('<uuid:uuid>/contacts/<int:contact_id>/edit/', views.edit_contact, name='edit_contact'),
    path('<uuid:uuid>/documents/', views.client_documents, name='client_documents'),
    path('<uuid:uuid>/add-document/', views.add_document, name='add_document'),
    path('<uuid:uuid>/cases/', views.client_cases, name='client_cases'),
]