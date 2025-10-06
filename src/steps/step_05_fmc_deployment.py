"""
Step 4: FTD Zone, Interface and Route Configuration

Configures Cisco FTD devices with security zones, interface settings, and static routes
through FMC REST API. This step handles the complete network configuration including
security zone creation, interface IP assignment, zone assignment, and default route creation.

Key Features:
- Security zone creation and management
- Physical interface configuration with IP addresses and security zone assignment
- Static route creation with gateway host objects
- HA-aware configuration targeting the primary device
- Comprehensive error handling and logging
"""

import requests
import logging
import pickle
import json
import sys
import os
import time

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step05_FMC_DEPLOYMENT:
    """
    Configure FTD security zones, interfaces, and routing.

    Uses credentials and device information from Jenkins form parameters.
    """
    
    def __init__(self):
        """
        Initialize FTD configuration step.
        """
        
    def execute(self):
        """
        Execute FTD zone, interface and route configuration.
        Uses credentials from Jenkins form parameters.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            
            self.load_devices_templates()
            self.fmc_ip = os.getenv('FMC_IP')

            with open('api_keys_data.pkl', 'rb') as f:
                rest_api_headers = pickle.load(f)
                   
            # FMC API endpoints
            fmc_ha_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs"
            fmc_ha_check_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}"
            url_devices_int = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/physicalinterfaces"
            fmc_obj_host_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/hosts"
            fmc_obj_network_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/networks"
            fmc_routing_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/routing/ipv4staticroutes"
            ha_monitored_interfaces = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}/monitoredinterfaces"
            ha_monitored_interfaces_detail = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}/monitoredinterfaces/{{matching_interface_id}}"
            deployable_devices = f'https://192.168.0.201/api/fmc_config/v1/domain/default/deployment/deployabledevices'


            ### GET Deployable devices ###
                
            deployable_dev_dict = {}
            response_deployable_devices = requests.get(deployable_devices, headers=rest_api_headers, verify=False)
            response_deployable_devices.raise_for_status()
            deployable_dev_json = response_deployable_devices.json().get('items', [])
            for dev in deployable_dev_json:
                name = dev.get('name')
                dev_version = dev.get('version')
                deployable_dev_dict[dev_version] = name
                logger.info("Deployable Devices:")
                logger.info(deployable_dev_dict)
                if name == self.ftd_ha_tmp['ha_payload']['name']:
                    #GET HA ID
                    response_ha_id = requests.get(fmc_ha_settings_url, headers=rest_api_headers, verify=False)
                    response_ha_id.raise_for_status()
                    ha_output = response_ha_id.json().get('items', [])
                    ha_id = ""
                    for ha in ha_output:
                        if ha.get('name') == self.ftd_ha_tmp['ha_payload']['name']:
                            ha_id = ha.get("id")
                            break
                logger.info("HA ID:")
                logger.info(ha_id)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False

        return True

    def load_devices_templates(self):
        from utils_ftd import FTD_HA_TEMPLATE,FTD_SEC_ZONES_TEMPLATE,FTD_INT_TEMPLATE,FTD_STATIC_ROUTE_TEMPLATE,FTD_HA_STANDBY_TEMPLATE

        with open(FTD_HA_TEMPLATE, 'r') as f0, \
            open(FTD_SEC_ZONES_TEMPLATE, 'r') as f1, \
            open(FTD_INT_TEMPLATE, 'r') as f2, \
            open(FTD_STATIC_ROUTE_TEMPLATE, 'r') as f3, \
            open(FTD_HA_STANDBY_TEMPLATE, 'r') as f4:
            
            self.ftd_ha_tmp = json.load(f0)
            logger.info("Loaded FTD HA template")
            self.ftd_sec_zones_tmp = json.load(f1)
            logger.info("Loaded FTD security zones template")
            self.fmc_int_settings = json.load(f2)
            logger.info("Loaded FTD interfaces configuration template")
            self.fmc_route_settings = json.load(f3)
            logger.info("Loaded FTD static route configuration template")
            self.fmc_ha_standby_settings = json.load(f4)
            logger.info("Loaded FTD HA standby IP configuration template")