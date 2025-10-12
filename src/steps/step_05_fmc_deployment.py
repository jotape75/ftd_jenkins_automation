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

from importlib import metadata
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
        self.devices_list = []  # Initialize an empty list to store devices
        self.device_names = []  # Initialize an empty list to store device names

    def load_devices_templates(self):
        from utils_ftd import EMAIL_REPORT_DATA_FILE, \
                              FTD_DEVICES_TEMPLATE, \
                              FTD_HA_TEMPLATE

        with open(EMAIL_REPORT_DATA_FILE, 'r') as f0,\
             open(FTD_DEVICES_TEMPLATE, 'r') as f1,\
             open(FTD_HA_TEMPLATE, 'r') as f2:
            self.email_report_data = json.load(f0)
            self.ftd_devices_tmp = json.load(f1)
            self.ftd_ha_tmp = json.load(f2)

    def save_report_data_file(self):
        from utils_ftd import EMAIL_REPORT_DATA_FILE

        with open(EMAIL_REPORT_DATA_FILE, 'w') as f:
            json.dump(self.email_report_data, f, indent=4)

    def _initialize_api_urls(self):
        self.fmc_device_health = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords?expanded=true"
        self.fmc_ha_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs"
        self.fmc_ha_check_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}"
        self.deployable_devices = f'https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/deployabledevices'
        self.deployment_requests = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/deploymentrequests"
        self.monitor_deployments = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/jobhistories?expanded=true"
        self.fmc_ha_status = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs?expanded=true"

    def devices_health_status(self):
        device_health_report = self.email_report_data.get("health_status", [])

        response_health = requests.get(self.fmc_device_health, headers=self.rest_api_headers, verify=False)
        response_health.raise_for_status()
        devices = response_health.json() # Get the first page of devices
        temp_devices_list = devices.get('items', []) # Get the list of devices

        for device in self.ftd_devices_tmp["device_payload"]:
            device_name = device.get("name")
            self.device_names.append(device_name)

        for fmc_device in temp_devices_list:
            device_name = fmc_device.get("name")
            if device_name in self.device_names:
                health = fmc_device.get("healthStatus", "").lower()
                deploy = fmc_device.get("deploymentStatus", "").upper()
                logger.info(f"Device {device_name} health status: '{health}' - deployment status: '{deploy}'")
   
                device_health_report.append({
                    'device_name': device_name,
                    'health_status': health,
                    'deployment_status': deploy
                })
        self.save_report_data_file()
        logger.info("Saved device health status to report data file")
        return True
    def ha_status(self):

        ha_status_report = self.email_report_data.get("ha_status", [])
        try:
            ha_payload = self.ftd_ha_tmp["ha_payload"]
            ha_payload_name = ha_payload.get("name")
            response_ha = requests.get(self.fmc_ha_status, headers=self.rest_api_headers, verify=False)
            response_ha.raise_for_status()
            ha_json = response_ha.json().get('items', [])
            ha_item = ha_json[0]
            ha_name = ha_item.get('name')
            metadata = ha_item.get('metadata', {})

            if ha_name == ha_payload_name:
                primary_device = metadata["primaryStatus"]["device"]["name"]
                secondary_device = metadata["secondaryStatus"]["device"]["name"]
                primary_status = metadata["primaryStatus"]["currentStatus"]
                secondary_status = metadata["secondaryStatus"]["currentStatus"]
                logger.info(f"HA Pair: {ha_name}, Primary: {primary_device} ({primary_status}), Secondary: {secondary_device} ({secondary_status})")
                ha_status_report.append({
                    'ha_name': ha_name,
                    'primary_device': primary_device,
                    'secondary_device': secondary_device,
                    'primary_status': primary_status,
                    'secondary_status': secondary_status
                })
                self.save_report_data_file()
                logger.info("Saved HA status to report data file")
                return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HA status: {e}")
            return False    

    def final_deployment_check(self):
        try:
             ### GET Deployable devices ###

            response_deployable_devices = requests.get(self.deployable_devices, headers=self.rest_api_headers, verify=False)
            response_deployable_devices.raise_for_status()
            deployable_dev_json = response_deployable_devices.json().get('items', [])

            if not deployable_dev_json:
                logger.info("No deployable devices found. All devices are up to date.")
                return True
            
            for dev in deployable_dev_json:
                name = dev.get('name')
                if name == self.ftd_ha_tmp['ha_payload']['name']:
                    dev_version = dev.get('version')
                    logger.info(f"Deployable Devices: {name}: {dev_version}")
                    #GET HA ID
                    response_ha_id = requests.get(self.fmc_ha_settings_url, headers=self.rest_api_headers, verify=False)
                    response_ha_id.raise_for_status()
                    ha_output = response_ha_id.json().get('items', [])
                    ha_id = ""
                    for ha in ha_output:
                        if ha.get('name') == self.ftd_ha_tmp['ha_payload']['name']:
                            ha_id = ha.get("id")
                            logger.info(f"HA ID: {ha_id}")
                            response_ha_check = requests.get(self.fmc_ha_check_url.format(ha_id=ha_id), headers=self.rest_api_headers, verify=False)
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
                            deployment_response = requests.post(self.deployment_requests, headers=self.rest_api_headers, data=json.dumps(deployment_payload), verify=False)
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
                                    monitor_response = requests.get(self.monitor_deployments, headers=self.rest_api_headers, verify=False)
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
    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False

        return True

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
            self._initialize_api_urls()
            with open('api_keys_data.pkl', 'rb') as f:
                self.rest_api_headers = pickle.load(f)
                   
            if not self.final_deployment_check():
               logger.error("Final deployment check failed")
               return False
            
            if not self.devices_health_status():
               logger.error("Failed to get devices health status")
               return False
            if not self.ha_status():
               logger.error("Failed to get HA status")
               return False
            
            logger.info("Final deployment completed successfully")
            return True
    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False


        # # FMC API endpoints
        # fmc_ha_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs"
        # fmc_ha_check_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}"
        # deployable_devices = f'https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/deployabledevices'
        # deployment_requests = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/deploymentrequests"
        # monitor_deployments = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/deployment/jobhistories?expanded=true"
    

        #    ### GET Deployable devices ###
                
        #     response_deployable_devices = requests.get(deployable_devices, headers=rest_api_headers, verify=False)
        #     response_deployable_devices.raise_for_status()
        #     deployable_dev_json = response_deployable_devices.json().get('items', [])

        #     if not deployable_dev_json:
        #         logger.info("No deployable devices found. All devices are up to date.")
        #         return True
            
        #     for dev in deployable_dev_json:
        #         name = dev.get('name')
        #         if name == self.ftd_ha_tmp['ha_payload']['name']:
        #             dev_version = dev.get('version')
        #             logger.info(f"Deployable Devices: {name}: {dev_version}")
        #             #GET HA ID
        #             response_ha_id = requests.get(fmc_ha_settings_url, headers=rest_api_headers, verify=False)
        #             response_ha_id.raise_for_status()
        #             ha_output = response_ha_id.json().get('items', [])
        #             ha_id = ""
        #             for ha in ha_output:
        #                 if ha.get('name') == self.ftd_ha_tmp['ha_payload']['name']:
        #                     ha_id = ha.get("id")
        #                     logger.info(f"HA ID: {ha_id}")
        #                     response_ha_check = requests.get(fmc_ha_check_url.format(ha_id=ha_id), headers=rest_api_headers, verify=False)
        #                     response_ha_check.raise_for_status()
        #                     ha_json = response_ha_check.json()
        #                     active_device = ha_json["metadata"]["primaryStatus"]["device"]["name"]
        #                     logger.info(f'Active device is {active_device}')
        #                     primary_status_id = ha_json["metadata"]["primaryStatus"]["device"]["id"]
        #                     logger.info(f"Primary Device ID: {primary_status_id}")
        #                     ### Perform Deployment ###
        #                     deployment_payload = {
        #                         "type": "DeploymentRequest",
        #                         "version": dev_version,
        #                         "forceDeploy": True,
        #                         "ignoreWarning": True,
        #                         "deviceList": [primary_status_id],
        #                         "deploymentNote": "Final deployment via Jenkins"
        #                     }
        #                     deployment_response = requests.post(deployment_requests, headers=rest_api_headers, data=json.dumps(deployment_payload), verify=False)
        #                     if deployment_response.status_code == 202:
        #                         logger.info(f"Deployment for {active_device} initiated successfully.")
        #                     else:
        #                         logger.error(f"Deployment initiation for {active_device} failed: {deployment_response.status_code} - {deployment_response.text}")
        #                         return False

        #                     # Monitor deployment status
        #                     timeout_counter = 0
        #                     max_timeout = 300
        #                     poll_interval = 10
                         
        #                     while timeout_counter < max_timeout:
        #                         try:
        #                             monitor_response = requests.get(monitor_deployments, headers=rest_api_headers, verify=False)
        #                             monitor_response.raise_for_status()
        #                             monitor_data = monitor_response.json().get('items', [])

        #                             # Check the latest job for our target device
        #                             latest_job = monitor_data[0]
        #                             device_list = latest_job.get('deviceList', [])
        #                             for device in device_list:
        #                                 if device.get("deviceUUID") == primary_status_id:
        #                                     device_name = device.get("deviceName")
        #                                     deployment_status = device.get("deploymentStatus")
        #                                     logger.info(f"Deployment status for {device_name}: {deployment_status} - {timeout_counter } seconds")
        #                                     if deployment_status == "SUCCEEDED":
        #                                         logger.info(f"Deployment for {device_name} completed successfully.")
        #                                         return True
        #                                     elif deployment_status == "FAILED":
        #                                         logger.error(f"Deployment for {device_name} failed. Check FMC for details.")
        #                                         return False
                                            
        #                             time.sleep(poll_interval)
        #                             timeout_counter += poll_interval
        #                         except Exception as e:
        #                             logger.error(f"Error while monitoring deployment: {e}")
        #                             time.sleep(poll_interval)
        #                             timeout_counter += poll_interval
    
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error: {e}")
        #     return False

        # return True

   