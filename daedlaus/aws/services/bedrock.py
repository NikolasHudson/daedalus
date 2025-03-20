import json
import logging

from ..utils import get_aws_session, get_active_bedrock_config, BOTO3_AVAILABLE

# Try to import boto3 dependencies, but handle gracefully if not available
if BOTO3_AVAILABLE:
    import boto3
    from botocore.exceptions import ClientError
else:
    # Create a dummy ClientError class if boto3 is not available
    class ClientError(Exception):
        pass

logger = logging.getLogger(__name__)

class BedrockService:
    """
    Service class for AWS Bedrock operations.
    """
    def __init__(self, config=None):
        """
        Initialize the Bedrock service with the given configuration.
        If no configuration is provided, use the active configuration.
        
        Args:
            config: BedrockConfiguration instance (optional)
        """
        if not BOTO3_AVAILABLE:
            logger.error("boto3 is not installed. Bedrock functionality will not work.")
            self.session = None
            self.client = None
            self.model_id = None
            self.config = None
            return
            
        if config is None:
            self.config = get_active_bedrock_config()
        else:
            self.config = config
            
        if self.config:
            try:
                self.session = get_aws_session(self.config)
                self.client = self.session.client(
                    service_name='bedrock-runtime',
                    region_name=self.config.region
                )
                self.model_id = self.config.default_model_id
            except Exception as e:
                logger.error(f"Error initializing Bedrock service: {str(e)}")
                self.session = None
                self.client = None
                self.model_id = None
        else:
            self.session = None
            self.client = None
            self.model_id = None
            logger.warning("No Bedrock configuration provided or available")
    
    def invoke_model(self, prompt, model_id=None, parameters=None):
        """
        Invoke a Bedrock model with the given prompt.
        
        Args:
            prompt: Text prompt to send to the model
            model_id: Model ID to use (defaults to configuration default)
            parameters: Model parameters as dictionary
            
        Returns:
            tuple: (success, response or error message)
        """
        if not self.client:
            return False, "No Bedrock client available - check configuration"
        
        # Use provided model ID or default from config
        model_id = model_id or self.model_id
        
        # Default parameters if none provided
        if parameters is None:
            parameters = {
                "max_tokens": 500,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        
        try:
            # Format request based on model provider
            if "anthropic.claude" in model_id or "us.anthropic.claude" in model_id:
                # Claude models use this format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": parameters.get("max_tokens", 500),
                    "temperature": parameters.get("temperature", 0.7),
                    "top_p": parameters.get("top_p", 0.9),
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            else:
                # Generic format for other models
                request_body = {
                    "prompt": prompt,
                    "max_tokens": parameters.get("max_tokens", 500),
                    "temperature": parameters.get("temperature", 0.7),
                    "top_p": parameters.get("top_p", 0.9),
                }
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response.get('body').read())
            
            # Extract the generated text based on model
            if "anthropic.claude" in model_id or "us.anthropic.claude" in model_id:
                # Claude models return this format
                if 'content' in response_body and len(response_body['content']) > 0:
                    generated_text = response_body['content'][0]['text']
                else:
                    generated_text = ""
            else:
                # Generic extraction for other models
                generated_text = response_body.get('completion', response_body.get('generated_text', ''))
            
            return True, generated_text
        
        except ClientError as e:
            logger.error(f"Error invoking Bedrock model: {str(e)}")
            return False, str(e)
    
    def list_available_models(self):
        """
        List available Bedrock models.
        
        Returns:
            list: List of available model IDs or empty list on error
        """
        if not self.session:
            return []
        
        try:
            # Create a bedrock client (not bedrock-runtime)
            bedrock_client = self.session.client(
                service_name='bedrock', 
                region_name=self.config.region
            )
            
            # List foundation models
            response = bedrock_client.list_foundation_models()
            
            # Extract model IDs
            models = [model.get('modelId') for model in response.get('modelSummaries', [])]
            return models
        
        except ClientError as e:
            logger.error(f"Error listing Bedrock models: {str(e)}")
            return []