from django.urls import path
from . import views

app_name = 'aws'

urlpatterns = [
    path('validate-aws-credentials/<str:app_label>/<str:model_name>/<int:object_id>/',
         views.validate_aws_credentials, name='validate_aws_credentials'),
    path('test-aws-connection/<str:app_label>/<str:model_name>/<int:object_id>/',
         views.test_aws_connection, name='test_aws_connection'),
    path('setup-guide/', views.setup_guide, name='setup_guide'),
]