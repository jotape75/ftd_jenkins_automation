"""
Step 2: FTD Device Registration with FMC

Registers Cisco FTD devices with Firepower Management Center (FMC) using 
device templates and credentials provided through Jenkins form parameters. 
This step handles device registration, policy assignment, and deployment 
status monitoring.

Key Features:
- Dynamic device template loading and policy assignment
- FMC REST API integration for device registration
- Health status and deployment monitoring with timeout handling
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

class Step03_HAConfig:
    """
    Configure High Availability (HA) settings for FTD devices.

    Uses credentials and device information from Jenkins form parameters.
    """
    
    def __init__(self):
        """
        Initialize FTD device registration step.
        """
        self.devices_list = []  # Initialize an empty list to store devices
        self.device_names = []  # Initialize an empty list to store device names
        self.poll_interval = 10

    def load_devices_templates(self):
        from utils_ftd import FTD_HA_TEMPLATE, FTD_DEVICES_TEMPLATE,EMAIL_REPORT_DATA_FILE

        with open(FTD_HA_TEMPLATE, 'r') as f0, \
             open(FTD_DEVICES_TEMPLATE, 'r') as f1:


            self.ftd_ha_tmp = json.load(f0)
            logger.info("Loaded FTD HA template")
            self.ftd_devices_tmp = json.load(f1)
            logger.info("Loaded FTD devices template")

    def _initialize_api_urls(self):

        """Initialize API URLs after fmc_ip is set"""
        self.fmc_ha_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs"
        self.fmc_ha_check_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}"
        self.fmc_devices = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords"
        self.fmc_dev_int_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{device_id}}/physicalinterfaces"
    def ha_configuration(self):
        try:
            response_ha = requests.get(self.fmc_devices, headers=self.rest_api_headers, verify=False)
            response_ha.raise_for_status()
            devices = response_ha.json() # Get the first page of devices
            temp_devices_list = devices.get('items', []) # Get the list of devices

            for name in self.ftd_devices_tmp["device_payload"]:
                self.device_names.append(name['name']) # Append the device name to the list

            for id in temp_devices_list:
                if id['name'] in self.device_names: # Only process devices in which names are in device_names
                    logger.info(f"Adding device {id['name']} - {id['id']} to HA pair configuration")
                    device_name = id['name'] # Get the name of each device
                    device_id = id['id'] # Get the ID of each device
                    response_int = requests.get(self.fmc_dev_int_url.format(device_id=device_id), headers=self.rest_api_headers, verify=False)
                    response_int.raise_for_status()
                    temp_devices_interface = response_int.json().get('items', [])
                    for interface in temp_devices_interface:
                        if interface['name'] == self.ha_interface:
                            interface_id = interface['id'] # Get the ID of each device interface
                            self.devices_list.append({"name": device_name, "id": device_id, "interface_id": interface_id}) # Append the device ID to the list
            
            ha_payload = self.ftd_ha_tmp["ha_payload"]
            ha_payload["primary"]["id"] = self.devices_list[0]["id"]
            ha_payload["primary"]["name"] = self.devices_list[0]["name"]
            ha_payload["secondary"]["id"] = self.devices_list[1]["id"]
            ha_payload["secondary"]["name"] = self.devices_list[1]["name"]
            ha_payload["ftdHABootstrap"]["lanFailover"]["interfaceObject"]["id"] = self.devices_list[0]["interface_id"]
            ha_payload["ftdHABootstrap"]["statefulFailover"]["interfaceObject"]["id"] = self.devices_list[1]["interface_id"]
            response_post = requests.post(self.fmc_ha_settings_url, headers=self.rest_api_headers, data=json.dumps(ha_payload), verify=False)
            time.sleep(10)
            # Poll until the new HA pair appears in the list
            ha_id = ""
            max_ha_wait = 1800
            wait_ha = 0
            while not ha_id:
                response_no_ha_id = requests.get(self.fmc_ha_settings_url, headers=self.rest_api_headers, verify=False)
                response_no_ha_id.raise_for_status()
                ha_pairs = response_no_ha_id.json().get('items', [])
                for ha in ha_pairs:
                    if ha.get('name') == ha_payload['name']:
                        ha_id = ha.get('id')
                        logger.info(f'HA pair found: {ha_id}')
                        break
                if not ha_id:
                    if wait_ha > max_ha_wait:
                        logger.info("Timeout waiting for HA pair to appear.")
                        return False
                    logger.info(f"Waiting for HA pair to be created... ({wait_ha}s)")
                    time.sleep(self.poll_interval)
                    wait_ha += self.poll_interval
            if ha_id:
                while True:
                    response_ha_id = requests.get(self.fmc_ha_check_url.format(ha_id=ha_id), headers=self.rest_api_headers, verify=False)
                    response_ha_id.raise_for_status()
                    ha_json = response_ha_id.json()
                    meta = ha_json.get('metadata', {})
                    primary_status = meta.get('primaryStatus', {}).get('currentStatus', '').lower()
                    secondary_status = meta.get('secondaryStatus', {}).get('currentStatus', '').lower()
                    logger.info(f"HA status: primary={primary_status}, secondary={secondary_status}")
                    if primary_status == "active" and secondary_status == "standby":
                        logger.info("HA added successfully.")
                        return True
                    if primary_status == "failed" or secondary_status == "failed":
                        logger.info("HA failed - Please check logs.")
                        return False
                    if wait_ha > max_ha_wait:
                        logger.info(f"Warning: HA taking too long to establish. Waited {wait_ha} seconds.")
                        return False
                    logger.info(f"Waiting... ({wait_ha}s)")
                    time.sleep(self.poll_interval)
                    wait_ha += self.poll_interval
            return False  # Fallback return if something goes wrong
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False

    def execute(self):
        """
        Execute FTD device registration with FMC.
        Uses credentials from Jenkins form parameters.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # devices_list = []  # Initialize an empty list to store devices
            # device_names = []  # Initialize an empty list to store device names
            # poll_interval = 10
            self.load_devices_templates()
           
            self._initialize_api_urls()
        
            self.fmc_ip = os.getenv('FMC_IP')
            self.ha_interface = os.getenv('HA_INTERFACE')

            with open('api_keys_data.pkl', 'rb') as f:
                self.rest_api_headers = pickle.load(f)

            if not self.ha_configuration():
                logger.error("HA configuration failed.")
                return False
            
            logger.info("HA configuration Completed Successfully")
            return True

            # # FMC API endpoints
            # fmc_ha_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs"
            # fmc_ha_check_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}"
            # fmc_devices = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords"
            # fmc_dev_int_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{device_id}}/physicalinterfaces"

            # response_ha = requests.get(fmc_devices, headers=rest_api_headers, verify=False)
            # response_ha.raise_for_status() 
            # devices = response_ha.json() # Get the first page of devices
            # temp_devices_list = devices.get('items', []) # Get the list of devices

            # for name in self.ftd_devices_tmp["device_payload"]:
            #     device_names.append(name['name']) # Append the device name to the list

            # for id in temp_devices_list:
            #     if id['name'] in device_names: # Only process devices in which names are in device_names
            #         logger.info(f"Adding device {id['name']} - {id['id']} to HA pair configuration")
            #         device_name = id['name'] # Get the name of each device
            #         device_id = id['id'] # Get the ID of each device
            #         response_int = requests.get(fmc_dev_int_url.format(device_id=device_id), headers=rest_api_headers, verify=False)
            #         response_int.raise_for_status()
            #         temp_devices_interface = response_int.json().get('items', [])
            #         for interface in temp_devices_interface:
            #             if interface['name'] == self.ha_interface:
            #                 interface_id = interface['id'] # Get the ID of each device interface
            #                 devices_list.append({"name": device_name, "id": device_id, "interface_id": interface_id}) # Append the device ID to the list
            
            # ha_payload = self.ftd_ha_tmp["ha_payload"]
            # ha_payload["primary"]["id"] = devices_list[0]["id"]
            # ha_payload["primary"]["name"] = devices_list[0]["name"]
            # ha_payload["secondary"]["id"] = devices_list[1]["id"]
            # ha_payload["secondary"]["name"] = devices_list[1]["name"]
            # ha_payload["ftdHABootstrap"]["lanFailover"]["interfaceObject"]["id"] = devices_list[0]["interface_id"]
            # ha_payload["ftdHABootstrap"]["statefulFailover"]["interfaceObject"]["id"] = devices_list[1]["interface_id"]
            # response_post = requests.post(fmc_ha_settings_url, headers=rest_api_headers, data=json.dumps(ha_payload), verify=False)
            # time.sleep(10)
            # # Poll until the new HA pair appears in the list
            # ha_id = ""
            # max_ha_wait = 1800
            # wait_ha = 0
            # while not ha_id:
            #     response_no_ha_id = requests.get(fmc_ha_settings_url, headers=rest_api_headers, verify=False)
            #     response_no_ha_id.raise_for_status()
            #     ha_pairs = response_no_ha_id.json().get('items', [])
            #     for ha in ha_pairs:
            #         if ha.get('name') == ha_payload['name']:
            #             ha_id = ha.get('id')
            #             logger.info(f'HA pair found: {ha_id}')
            #             break
            #     if not ha_id:
            #         if wait_ha > max_ha_wait:
            #             logger.info("Timeout waiting for HA pair to appear.")
            #             return False
            #         logger.info(f"Waiting for HA pair to be created... ({wait_ha}s)")
            #         time.sleep(poll_interval)
            #         wait_ha += poll_interval
            # if ha_id:
            #     while True:
            #         response_ha_id = requests.get(fmc_ha_check_url.format(ha_id=ha_id), headers=rest_api_headers, verify=False)
            #         response_ha_id.raise_for_status()
            #         ha_json = response_ha_id.json()
            #         meta = ha_json.get('metadata', {})
            #         primary_status = meta.get('primaryStatus', {}).get('currentStatus', '').lower()
            #         secondary_status = meta.get('secondaryStatus', {}).get('currentStatus', '').lower()
            #         logger.info(f"HA status: primary={primary_status}, secondary={secondary_status}")
            #         if primary_status == "active" and secondary_status == "standby":
            #             logger.info("HA added successfully.")
            #             return True
            #         if primary_status == "failed" or secondary_status == "failed":
            #             logger.info("HA failed - Please check logs.")
            #             return False
            #         if wait_ha > max_ha_wait:
            #             logger.info(f"Warning: HA taking too long to establish. Waited {wait_ha} seconds.")
            #             return False
            #         logger.info(f"Waiting... ({wait_ha}s)")
            #         time.sleep(poll_interval)
            #         wait_ha += poll_interval
            # return False  # Fallback return if something goes wrong

        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
        
    