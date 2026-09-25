"""
Example API client demonstrating secure usage of PRIVATE_KEY.

This module shows how to properly use the private key from
environment variables without exposing it in logs or code.
"""

import logging
from core.config import get_private_key, ConfigurationError

# Configure logging (never log sensitive data!)
logger = logging.getLogger(__name__)


class APIClient:
    """
    Example API client that uses the private key securely.
    
    This demonstrates best practices for handling sensitive credentials.
    """
    
    def __init__(self):
        """
        Initialize the API client with secure credentials.
        
        Raises:
            ConfigurationError: If PRIVATE_KEY is not configured.
        """
        try:
            self._api_key = get_private_key()
            logger.info("API client initialized successfully")
        except ConfigurationError as e:
            logger.error("Failed to initialize API client: Configuration error")
            raise
    
    def make_api_call(self, endpoint: str, data: dict = None) -> dict:
        """
        Make an API call using the private key.
        
        Args:
            endpoint: The API endpoint to call.
            data: Optional data to send with the request.
            
        Returns:
            dict: The API response.
            
        Note:
            This is a placeholder implementation. Replace with actual API logic.
        """
        # SECURITY: Never log the actual key value!
        logger.info(f"Making API call to endpoint: {endpoint}")
        
        # Example: Use the key in headers (actual implementation would use requests library)
        headers = {
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json'
        }
        
        # Your actual API call logic here
        # response = requests.post(endpoint, json=data, headers=headers)
        
        logger.info("API call completed successfully")
        return {"status": "success", "message": "API call completed"}
    
    def validate_key(self) -> bool:
        """
        Validate that the API key is properly formatted.
        
        Returns:
            bool: True if key appears valid, False otherwise.
        """
        # Example validation (adjust based on your key format)
        if not self._api_key:
            return False
        
        # Check if key has expected prefix (example: sk-or-v1-)
        if self._api_key.startswith('sk-or-v1-'):
            logger.info("API key format validation passed")
            return True
        
        logger.warning("API key format validation failed")
        return False


def get_api_client() -> APIClient:
    """
    Factory function to get an initialized API client.
    
    Returns:
        APIClient: Configured API client instance.
        
    Raises:
        ConfigurationError: If configuration is invalid.
        
    Example:
        >>> from sitemap_app.api_client import get_api_client
        >>> client = get_api_client()
        >>> response = client.make_api_call('/generate', {'prompt': 'test'})
    """
    return APIClient()
