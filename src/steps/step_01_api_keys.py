"""
Step 1: API Key Generation for PA Firewalls

Generates API keys for multiple Palo Alto firewall devices using credentials
provided through Jenkins form parameters. This step authenticates with each
firewall device and creates the necessary API keys for subsequent automation
steps. The generated keys are saved to a pickle file for use by other steps.

Key Features:
- Dynamic credential loading from Jenkins environment variables
- Multi-device API key generation with error handling
- Saves API keys and credentials for downstream automation steps
"""

from wsgiref import headers
import requests
import logging
import pickle
import json
import xml.etree.ElementTree as ET
import sys
import os

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step01_APIKeys:
    """
    Generate API keys for FMC.
    
    Uses credentials and firewall hosts from Jenkins form parameters.
    """
    
    def __init__(self):
        """
        Initialize API key generation step.
        """
        self.rest_api_headers = {
            "Content-Type": "application/json",
        }
    
    def _get_credentials_from_jenkins(self):
        """
        Get firewall credentials from Jenkins environment variables.
        
        Returns:
            list: List of firewall credentials
        """
        try:
            # Get credentials from Jenkins form parameters
            self.username = os.getenv('USERNAME')
            self.password = os.getenv('PASSWORD')
            self.fmc_ip = os.getenv('FMC_IP')

            if not self.username or not self.password or not self.fmc_ip:
                raise Exception("USERNAME, PASSWORD, and FMC_IP must be specified in Jenkins form")

            # Create credentials list
            
            logger.info(f"Loaded credentials for FMC from Jenkins parameters")
            logger.info(f"FMC: {self.fmc_ip}")
            logger.info(f"Username: {self.username}")

        except Exception as e:
            logger.error(f"Error getting credentials from Jenkins: {e}")
            raise
    
    def execute(self):
        """
        Execute API key generation for all devices.
        Uses credentials from Jenkins form parameters.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:

            self._get_credentials_from_jenkins()

            # Get credentials from Jenkins form parameters
            fmc_token = f"https://{self.fmc_ip}/api/fmc_platform/v1/auth/generatetoken"

            # Generate Token
            response_token = requests.post(fmc_token, headers=self.rest_api_headers, auth=(self.username, self.password), verify=False)
            response_token.raise_for_status()
            # Extract tokens from headers
            auth_token = response_token.headers.get("X-auth-access-token", None)
            if not auth_token:
                raise Exception("Authentication token not found in response.")
            
            logger.info(f"Authentication successful! Token: {auth_token}")
            self.rest_api_headers["X-auth-access-token"] = auth_token
            # Save to simple file for next steps to use
            
            with open('api_keys_data.pkl', 'wb') as f:
                pickle.dump(self.rest_api_headers, f)

            logger.info(f"Successfully generated and saved API keys for {self.fmc_ip}")
            logger.info(f"API keys saved to api_keys_data.pkl")
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in API key generation: {e}")
            return False