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
            deployable_devices = f'https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/deployabledevices'
            deployment_requests = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/deploymentrequests"
            monitor_deployments = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/jobhistories?expanded=true"
            ### GET Deployable devices ###
                
            response_deployable_devices = requests.get(deployable_devices, headers=rest_api_headers, verify=False)
            response_deployable_devices.raise_for_status()
            deployable_dev_json = response_deployable_devices.json().get('items', [])
            for dev in deployable_dev_json:
                name = dev.get('name')
                if name == self.ftd_ha_tmp['ha_payload']['name']:
                    dev_version = dev.get('version')
                    logger.info(f"Deployable Devices: {name}: {dev_version}")
                    #GET HA ID
                    response_ha_id = requests.get(fmc_ha_settings_url, headers=rest_api_headers, verify=False)
                    response_ha_id.raise_for_status()
                    ha_output = response_ha_id.json().get('items', [])
                    ha_id = ""
                    for ha in ha_output:
                        if ha.get('name') == self.ftd_ha_tmp['ha_payload']['name']:
                            ha_id = ha.get("id")
                            logger.info(f"HA ID: {ha_id}")
                            response_ha_check = requests.get(fmc_ha_check_url.format(ha_id=ha_id), headers=rest_api_headers, verify=False)
                            response_ha_check.raise_for_status()
                            ha_json = response_ha_check.json()
                            active_device = ha_json["metadata"]["primaryStatus"]["device"]["name"]
                            logger.info(f'Active device is {active_device}')
                            primary_status_id = ha_json["metadata"]["primaryStatus"]["device"]["id"]
                            logger.info(f"Primary Device ID: {primary_status_id}")
                            ### Perform Deployment ###
                            deployment_payload = {
                                "type": "DeploymentRequest",
                                "version": dev_version,
                                "forceDeploy": True,
                                "ignoreWarning": True,
                                "deviceList": [primary_status_id],
                                "deploymentNote": "Final deployment via Jenkins"
                            }
                            deployment_response = requests.post(deployment_requests, headers=rest_api_headers, data=json.dumps(deployment_payload), verify=False)
                            if deployment_response.status_code == 202:
                                logger.info(f"Deployment for {active_device} initiated successfully.")
                            else:
                                logger.error(f"Deployment initiation for {active_device} failed: {deployment_response.status_code} - {deployment_response.text}")
                                return False

                            # Monitor deployment status
                            timeout_counter = 0
                            max_timeout = 300
                            poll_interval = 10
                         
                            while timeout_counter < max_timeout:
                                try:
                                    monitor_response = requests.get(monitor_deployments, headers=rest_api_headers, verify=False)
                                    monitor_response.raise_for_status()
                                    monitor_data = monitor_response.json().get('items', [])

                                    # Check the latest job for our target device
                                    latest_job = monitor_data[0]
                                    device_list = latest_job.get('deviceList', [])
                                    for device in device_list:
                                        if device.get("deviceUUID") == primary_status_id:
                                            device_name = device.get("deviceName")
                                            deployment_status = device.get("deploymentStatus")
                                            logger.info(f"Deployment status for {device_name}: {deployment_status} - {timeout_counter } seconds")
                                            if deployment_status == "SUCCEEDED":
                                                logger.info(f"Deployment for {device_name} completed successfully.")
                                                return True
                                            elif deployment_status == "FAILED":
                                                logger.error(f"Deployment for {device_name} failed. Check FMC for details.")
                                                return False
                                            
                                    time.sleep(poll_interval)
                                    timeout_counter += poll_interval
                                except Exception as e:
                                    logger.error(f"Error while monitoring deployment: {e}")
                                    time.sleep(poll_interval)
                                    timeout_counter += poll_interval
                else:
                    logger.info(f"No Deployment Pending for Device {name}, skipping.")
                    continue
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