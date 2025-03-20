from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('upload/', views.document_upload, name='document_upload'),
    path('<uuid:uuid>/', views.document_detail, name='document_detail'),
    path('<uuid:uuid>/download/', views.document_download, name='document_download'),
    path('<uuid:uuid>/download/<int:version>/', views.document_download, name='document_download_version'),
]