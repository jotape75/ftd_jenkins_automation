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

class Step02_ADD_DEV_FMC:
    """
    Register FTD devices with FMC.
    
    Uses credentials and device information from Jenkins form parameters.
    """
    
    def __init__(self):
        """
        Initialize FTD device registration step.
        """

        self.ready_devices = {}
        self.poll_interval = 10
        self.waited = 0
        self.device_names = []
        self.devices_list = []

    def load_devices_templates(self):

        from utils_ftd import FTD_DEVICES_TEMPLATE, EMAIL_REPORT_DATA_FILE

        with open(FTD_DEVICES_TEMPLATE, 'r') as f ,\
            open(EMAIL_REPORT_DATA_FILE, 'r') as f2:
            self.ftd_devices_tmp = json.load(f)  
            logger.info("Loaded FTD devices template")
            self.email_report_data = json.load(f2)
            logger.info("Loaded email report data template")

    def _initialize_api_urls(self):

        """Initialize API URLs after fmc_ip is set"""
        self.fmc_access_policy_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/policy/accesspolicies"
        self.fmc_devices = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords"
        self.fmc_device_details_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{device_id}}"

    def save_report_data_file(self):
        from utils_ftd import EMAIL_REPORT_DATA_FILE

            # Save email report data dictionary to JSON file
        with open(EMAIL_REPORT_DATA_FILE, 'w') as f:
            json.dump(self.email_report_data, f, indent=4)

   
    def fmc_device_registration(self):
        """
        Register FTD devices with FMC.
        
        Returns:
            bool: True if successful, False otherwise
        """
        access_control_report = self.email_report_data.get("access_policies", [])
        try:
            # Retrieve Access Control Policy ID
            response_policy = requests.get(self.fmc_access_policy_url, headers=self.rest_api_headers, verify=False)
            response_policy.raise_for_status()
            policies = response_policy.json().get('items', [])
            policy_id = None
            for policy in policies:
                if policy["name"] == "Initial_policy":
                    policy_id = policy["id"]
                    access_control_report.append({
                        "name": policy["name"],
                        "id": policy_id,
                        "type": "Access Control Policy",
                        "status": "existing"
                    })
                    self.save_report_data_file()
                    logger.info("Email report data file updated with Access Control Policy.")
                    break
                    

            if not policy_id:
                logger.error("Initial_policy not found.")
                return False

            # Assign policy ID to each device
            for device in self.ftd_devices_tmp["device_payload"]:
                device["accessPolicy"]["id"] = policy_id
                logger.info(f"Assigned policy ID {policy_id} to device {device['name']}")

            # Register devices to FMC
            for device in self.ftd_devices_tmp["device_payload"]:
                device_name = device["name"]
                response_device = requests.post(self.fmc_devices, headers=self.rest_api_headers, data=json.dumps(device), verify=False)
                if response_device.status_code == 202:
                    logger.info(f"Device {device_name} added successfully to FMC.")
                else:
                    logger.error(f"Failed to add device {device_name} to FMC. Status code: {response_device.status_code}")
                    logger.error(response_device.text)
                    
            for name in self.ftd_devices_tmp["device_payload"]:
                self.device_names.append(name['name'])
                
            # Wait for all devices to appear in FMC device records
            max_wait = 600  # seconds
            waited_rec = 0 
            poll_interval = 10 
            pool_interval_reg = 30
            
            while True:
                response_show = requests.get(self.fmc_devices, headers=self.rest_api_headers, verify=False)
                response_show.raise_for_status()
                devices = response_show.json().get('items', [])
                found_device_names = [dev["name"] for dev in devices]
                missing_devices = set(self.device_names) - set(found_device_names)

                if not missing_devices:
                    logger.info("All devices have appeared in FMC device records.")
                    break
                    
                if waited_rec > max_wait:
                    logger.error(f"Timeout: Devices {missing_devices} did not appear in FMC device records after {max_wait} seconds.")
                    return False
                    
                logger.info(f"Waiting for devices to appear in FMC: {missing_devices} ({waited_rec}s)")
                time.sleep(poll_interval)
                waited_rec += poll_interval
                
            while True:
                response_health_status = requests.get(self.fmc_devices, headers=self.rest_api_headers, verify=False)
                response_health_status.raise_for_status()
                devices = response_health_status.json().get('items', [])
                
                for dev in devices:
                    if dev["name"] in self.device_names:
                        detail_resp = requests.get(self.fmc_device_details_url.format(device_id=dev['id']), headers=self.rest_api_headers, verify=False)
                        detail_resp.raise_for_status()
                        dev_detail = detail_resp.json()
                        health = dev_detail.get("healthStatus", "").lower()
                        deploy = dev_detail.get("deploymentStatus", "").upper()
                        logger.info(f"Device {dev['name']} healthStatus: {health}, deploymentStatus: {deploy}")
                        
                        healthy_states = ["green", "yellow", "recovered"]
                        if health in healthy_states and deploy == "DEPLOYED" and dev["name"] not in self.ready_devices:
                            self.ready_devices[dev["name"]] = dev

                        if health == "red" and deploy == "NOT_DEPLOYED":
                            logger.info(f"Device {dev['name']} is not deployed. Please check logs...")
                            continue
                            
                if missing_devices:
                    logger.error(f"Device(s) {missing_devices} are no longer present in FMC device records. Registration or deployment likely failed.")
                    break

                if len(self.ready_devices) == len(self.device_names):
                    logger.info("All devices are ready and deployed!")
                    break

                if self.waited > 1800:  # 30 minutes, just as a warning
                    logger.info(f"Warning: Devices are taking longer than expected to be ready. Waited {self.waited} seconds.")

                logger.info(f"Waiting... ({self.waited}s)")
                time.sleep(pool_interval_reg)
                self.waited += pool_interval_reg

            if len(self.ready_devices) < len(self.device_names):
                logger.error("Timeout waiting for devices to be ready.")
                return False
                
            logger.info("FTD device registration completed successfully!")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during device registration: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error in device registration: {e}")
            return False
    def execute(self):
        """
        Execute FTD device registration with FMC.
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

            if not self.fmc_device_registration():
                logger.error("Device registration failed.")
                return False
            logger.info("FTD device registration step completed successfully.")
            return True
        
        except Exception as e:
            logger.error(f"Unexpected error in device registration: {e}")
            return False
    
       
