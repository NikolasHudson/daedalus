from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.apps import apps
from django.urls import reverse
from django.http import JsonResponse, FileResponse
import logging
import os
from django.conf import settings


@staff_member_required
def validate_aws_credentials(request, app_label, model_name, object_id):
    """
    Validates AWS credentials for the specified model instance and redirects back
    to the admin page with a status message.
    """
    # Get the model class
    try:
        model = apps.get_model(app_label=app_label, model_name=model_name)
    except LookupError:
        messages.error(request, f"Invalid model: {app_label}.{model_name}")
        return redirect('admin:index')
    
    # Get the instance
    try:
        instance = get_object_or_404(model, pk=object_id)
    except:
        messages.error(request, f"Object with ID {object_id} not found")
        return redirect('admin:index')
    
    # Check if boto3 is available
    try:
        import boto3
        boto3_available = True
    except ImportError:
        boto3_available = False
        messages.error(request, "boto3 is not installed. Please install boto3 to validate AWS credentials.")
        return redirect(reverse(f'admin:{app_label}_{model_name}_change', args=[object_id]))
    
    if not boto3_available:
        messages.error(request, "boto3 is required for AWS credential validation but is not installed")
        return redirect(reverse(f'admin:{app_label}_{model_name}_change', args=[object_id]))
    
    try:
        # Run the validation
        success, message = instance.validate_credentials()
        
        # Add a message based on the validation result
        if success:
            messages.success(request, f"Validation successful: {message}")
        else:
            messages.error(request, f"Validation failed: {message}")
    except Exception as e:
        # Handle any exceptions
        import traceback
        error_details = traceback.format_exc()
        messages.error(request, f"Validation error: {str(e)}")
        logger = logging.getLogger(__name__)
        logger.error(f"AWS validation error: {error_details}")
    
    # Redirect back to the admin page
    return redirect(
        reverse(f'admin:{app_label}_{model_name}_change', args=[object_id])
    )


@staff_member_required
def test_aws_connection(request, app_label, model_name, object_id):
    """
    API endpoint for testing AWS connections asynchronously using AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    # Get the model class
    model = apps.get_model(app_label=app_label, model_name=model_name)
    # Get the instance
    instance = get_object_or_404(model, pk=object_id)
    
    try:
        # Run the validation
        success, message = instance.validate_credentials()
        
        return JsonResponse({
            'success': success,
            'message': message
        })
    except Exception as e:
        # Handle any exceptions
        return JsonResponse({
            'success': False,
            'message': f"Error: {str(e)}"
        }, status=500)

@staff_member_required
def setup_guide(request):
    """
    View to display the AWS setup guide.
    """
    setup_path = os.path.join(settings.STATIC_ROOT, 'aws/docs/setup.txt')
    context = {
        'title': 'AWS Setup Guide',
        'setup_guide': open(setup_path).read() if os.path.exists(setup_path) else 'Setup guide not found.'
    }
    return render(request, 'admin/aws/setup_guide.html', context)