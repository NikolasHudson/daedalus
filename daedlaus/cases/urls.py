from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('create/', views.case_create, name='case_create'),
    path('<uuid:uuid>/', views.case_detail, name='case_detail'),
    path('<uuid:uuid>/edit/', views.case_edit, name='case_edit'),
    path('<uuid:uuid>/folders/', views.folder_list, name='folder_list'),
    path('<uuid:uuid>/folders/create/', views.folder_create, name='folder_create'),
    path('<uuid:uuid>/documents/', views.case_documents, name='case_documents'),
    path('<uuid:uuid>/add-document/', views.add_document, name='add_document'),
]