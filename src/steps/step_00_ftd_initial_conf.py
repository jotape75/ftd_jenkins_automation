"""
Step 0: FTD Initial Configuration

Configures FTD devices with initial manager settings to connect to FMC.
This step establishes the SSH connection to each FTD device and configures
the manager registration for subsequent FMC management.

Key Features:
- Dynamic credential loading from Jenkins environment variables
- SSH-based FTD initial configuration with error handling
- Interactive prompt handling for manager registration
"""

import logging
import json
import sys
import os
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
import time

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger()

class Step00_FTDInitialConf:
    """
    Configure FTD devices for initial manager registration.
    
    Uses credentials and firewall hosts from Jenkins form parameters.
    """
    
    def __init__(self):
        """
        Initialize FTD initial configuration step.
        """
        pass
        
    def execute(self):
        """
        Execute FTD initial configuration for all devices.
        Uses credentials from Jenkins form parameters.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.load_devices_templates()

            # Get credentials from Jenkins form parameters
            self.username = os.getenv('SSH_ADMIN_USERNAME')
            self.password = os.getenv('SSH_ADMIN_PASSWORD')
            self.fmc_ip = os.getenv('FMC_IP')

            if not self.username or not self.password:
                raise Exception("SSH_ADMIN_USERNAME, SSH_ADMIN_PASSWORD must be specified in Jenkins form")

            logger.info(f"Loaded credentials for FTD from Jenkins parameters")
            logger.info(f"Username: {self.username}")

            for data in self.ftd_devices_tmp["device_payload"]:
                device = {
                    'device_type': 'cisco_ftd',
                    'host': data['hostName'],
                    'username': self.username,
                    'password': self.password,  
                }
                try:
                    logger.info(f"Connecting to FTD device {data['name']} at {data['hostName']}...")
                    with ConnectHandler(**device) as net_connect:
                        logger.info(f"Connected to {data['name']}. Sending initial configuration commands...")
                        
                        # Send the manager add command
                        commands = f'configure manager add {self.fmc_ip} {data["regKey"]}'
                        logger.info(f"Sending command: {commands}")
                        
                        # Use send_command_timing to handle interactive prompts
                        output_1 = net_connect.send_command_timing(
                            commands, 
                            delay_factor=3,
                            read_timeout=30
                        )
                        logger.info(f"Command output: {output_1}")
                        
                        # Check for confirmation prompt and respond
                        expect_string_01 = 'Do you want to continue[yes/no]:'
                        if expect_string_01 in output_1:
                            logger.info("Confirmation prompt detected, sending 'yes'")
                            output_2 = net_connect.send_command_timing('yes', delay_factor=3)
                            logger.info(f"Confirmation response: {output_2}")
                        else:
                            logger.warning(f"Expected confirmation prompt not found for {data['name']}")
                            logger.info(f"Full command output was: {output_1}")
                            output_2 = output_1
                            
                        # Check for registration success and get manager status
                        expect_string_02 = 'Please make note of reg_key as this will be required while adding Device in FMC.'
                        if expect_string_02 in output_1 or expect_string_02 in output_2:
                            logger.info("Manager registration successful, checking status")
                            try:
                                output_3 = net_connect.send_command('show managers', delay_factor=5, read_timeout=30)
                                logger.info(f"Manager status on {data['name']}:\n{output_3}")
                            except Exception as show_error:
                                logger.warning(f"Could not get manager status for {data['name']}: {show_error}")
                        else:
                            logger.warning("Manager registration confirmation not found")
                            logger.info(f"Registration output: {output_2}")
                            
                except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                    logger.error(f"Connection error for device {data['name']} at {data['hostName']}: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error for device {data['name']} at {data['hostName']}: {type(e).__name__}: {str(e)}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    return False
                    
            logger.info("FTD initial configuration completed successfully for all devices")
            return True
            
        except Exception as e:  
            logger.error(f"Unexpected error in FTD initial configuration: {e}")
            return False

    def load_devices_templates(self):
        from utils_ftd import FTD_DEVICES_TEMPLATE

        with open(FTD_DEVICES_TEMPLATE, 'r') as f:
            self.ftd_devices_tmp = json.load(f)  
            logger.info("Loaded FTD devices template")