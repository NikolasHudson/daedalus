# AWS Integration Module

This Django app provides AWS service integration for the Daedalus Legal Tech Platform.

## Features

- Secure storage and management of AWS credentials
- Admin interfaces for configuring AWS services
- S3 integration for document storage
- AWS Bedrock integration for AI capabilities
- Validation of AWS credentials and connections
- Service-specific utilities for AWS interactions

## Models

- `BaseAWSConfiguration`: Abstract base model for AWS credentials
- `S3Configuration`: Storage for S3 bucket settings and credentials
- `BedrockConfiguration`: Storage for AWS Bedrock settings and credentials

## Usage

### S3 Configuration

1. Navigate to the Django admin interface
2. Go to "AWS Configuration" > "S3 Configurations"
3. Add a new S3 configuration with:
   - AWS credentials (access key and secret key)
   - Region settings
   - Bucket name and configuration options
4. Validate the credentials using the "Validate Now" button

### Bedrock Configuration

1. Navigate to the Django admin interface
2. Go to "AWS Configuration" > "Bedrock Configurations"
3. Add a new Bedrock configuration with:
   - AWS credentials (access key and secret key)
   - Region settings (must be a Bedrock-supported region)
   - Default model ID
4. Validate the credentials using the "Validate Now" button

## Security

- AWS credentials are stored securely in the database
- Validation is performed within the application
- Only users with appropriate permissions can access credential management

## Dependencies

- boto3: Required for AWS interactions
- django-storages: For S3 storage integration

## Installation

1. Ensure boto3 is installed: `pip install boto3`
2. Ensure the 'aws' app is included in your INSTALLED_APPS setting
3. Run migrations: `python manage.py migrate aws`

## Running the Application Locally

To run the application locally with SQLite:

```bash
# Use the local settings module
export DJANGO_SETTINGS_MODULE=daedlaus.settings.local

# Apply migrations
python manage.py migrate

# Create a superuser if needed
python manage.py createsuperuser

# Run the server
python manage.py runserver
```

Access the admin interface at http://localhost:8000/admin/

### Required Dependencies

For AWS functionality to work correctly, make sure boto3 is installed:

```bash
pip install boto3
```

If boto3 is not installed, the AWS validation features will display appropriate error messages.

## Troubleshooting

If you encounter errors connecting to AWS services:

1. Verify your AWS credentials are correct
2. Ensure boto3 is properly installed
3. Check network connectivity to AWS services
4. Verify that the specified region supports the requested service
5. Check IAM permissions for the provided credentials

For detailed setup instructions, see the [setup.txt](setup.txt) file.