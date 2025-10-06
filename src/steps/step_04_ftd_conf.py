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

class Step04_FTD_CONF:
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
            fmc_sec_zones_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/securityzones"
            fmc_url_devices_int_detail = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/physicalinterfaces/{{interface_id}}"
            fmc_ha_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs"
            fmc_ha_check_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}"
            url_devices_int = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/physicalinterfaces"
            fmc_obj_host_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/hosts"
            fmc_obj_network_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/networks"
            fmc_routing_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/routing/ipv4staticroutes"
            ha_monitored_interfaces = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}/monitoredinterfaces"
            ha_monitored_interfaces_detail = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}/monitoredinterfaces/{{matching_interface_id}}"
            ## CREATE SECURITY ZONES ###

            zones_id_list = []
            get_zones = requests.get(fmc_sec_zones_url, headers=rest_api_headers, verify=False)
            get_zones.raise_for_status()
            existing_zones = get_zones.json().get('items', [])
            for zones in existing_zones:
                if zones.get('name') not in self.ftd_sec_zones_tmp["sec_zones_payload"]:
                    
                    for zone in self.ftd_sec_zones_tmp["sec_zones_payload"]:
                        response_zones = requests.post(fmc_sec_zones_url, headers=rest_api_headers, data=json.dumps(zone), verify=False)
                        response_zones.raise_for_status()
                        zones = response_zones.json()
                        zones_id = zones.get('id')
                        zones_id_list.append(zones_id)

                        if response_zones.status_code in [200, 201]:
                            logger.info(f"Security zone {zone['name']} created successfully.")
                        else:
                            logger.info(f"Failed to create security zone {zone['name']}. Status code: {response_zones.status_code}")
                            logger.info(response_zones.text)
                            return False
                else:
                    zones_id_list.append(zones.get('id'))
                    logger.info(f"Security zone {zones.get('name')} already exists. Skipping creation.")

            time.sleep(5)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
        
        ### CONFIGURE INTERFACES ###
        # try:
        # # Get the HA primary device ID
        #     def configure_interface(
        #         interface_id,
        #         interface_name,
        #         config,  # dict from your external config, includes zone_index
        #         zones_id_list,
        #         primary_status_id,
        #         primary_name,
        #         headers
        #     ):
        #         """
        #         Helper to configure a single interface on the FMC device using external config.
        #         """

        #         response_int = requests.get(fmc_url_devices_int_detail.format(primary_status_id=primary_status_id,interface_id=interface_id), headers=headers, verify=False)
        #         response_int.raise_for_status()
        #         interface_obj = response_int.json()
        #         interface_obj.pop("links", None)
        #         interface_obj.pop("metadata", None)
        #         # Use zone_index from config to select the correct security zone
        #         zone_index = config["zone_index"]
        #         interface_obj["securityZone"] = {
        #             "id": zones_id_list[zone_index],
        #             "type": "SecurityZone"
        #         }
        #         interface_obj["ifname"] = config["ifname"]
        #         interface_obj["enabled"] = True
        #         interface_obj["ipv4"] = {
        #             "static": {
        #                 "address": config["ip_address"],
        #                 "netmask": config["netmask"]
        #             }
        #         }
        #         response_put = requests.put(fmc_url_devices_int_detail.format(primary_status_id=primary_status_id,interface_id=interface_id), headers=rest_api_headers, data=json.dumps(interface_obj), verify=False)
        #         response_put.raise_for_status()
        #         if response_put.status_code in [200, 201]:
        #             logger.info(f"Security zone assigned to interface {interface_name} on device {primary_name} successfully.")
        #             logger.info(f'IP address assigned to interface {interface_name} on device {primary_name} successfully.')
        #         else:
        #             logger.info(f"Failed to assign security zone to interface {interface_name} on device {primary_name}. Status code: {response_put.status_code}")
        #             logger.info(response_put.text)
        #     time.sleep(15)
            
            #GET HA ID
            response_ha_id = requests.get(fmc_ha_settings_url, headers=rest_api_headers, verify=False)
            response_ha_id.raise_for_status()
            ha_output = response_ha_id.json().get('items', [])
            ha_id = ""
            for ha in ha_output:
                if ha.get('name') == self.ftd_ha_tmp['ha_payload']['name']:
                    ha_id = ha.get("id")
                    break
        #     response_ha_check = requests.get(fmc_ha_check_url.format(ha_id=ha_id), headers=rest_api_headers, verify=False)
        #     response_ha_check.raise_for_status()
        #     ha_json = response_ha_check.json()
        #     logger.info(f'Active device is {ha_json["metadata"]["primaryStatus"]["device"]["name"]}')
        #     logger.info(response_ha_check.text)
        #     primary_status_id = ha_json["metadata"]["primaryStatus"]["device"]["id"]
        #     primary_name = ha_json["metadata"]["primaryStatus"]["device"]["name"]
        #     response_int_check = requests.get(url_devices_int.format(primary_status_id=primary_status_id), headers=rest_api_headers, verify=False)
        #     response_int_check.raise_for_status()
        #     interfaces = response_int_check.json().get('items', [])

        #     for int_id in interfaces:
        #         int_name = int_id['name']
        #         if int_name  in self.fmc_int_settings:
        #             config = self.fmc_int_settings[int_name]
        #             configure_interface(
        #                 interface_id=int_id['id'],
        #                 interface_name=int_name,
        #                 config=config,
        #                 zones_id_list=zones_id_list,
        #                 primary_status_id=primary_status_id,
        #                 primary_name=primary_name,
        #                 headers=rest_api_headers
        #             )
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error: {e}")
        #     return False
            
        ### CREATE DEFAULT ROUTE ###

        # try:
        #     host_object = self.fmc_route_settings["host_object"]
        #     static_route_payload = self.fmc_route_settings["static_route_payload"]

        #     # Create network object:
        #     response_post = requests.post(fmc_obj_host_url, headers=rest_api_headers, data=json.dumps(host_object), verify=False)
        #     obj_creation_re = response_post.json()
        #     logger.info(response_post.status_code)
        #     if response_post.status_code in [200,201]:
        #         gw_host_id = obj_creation_re.get('id')
        #         static_route_payload["gateway"]["object"]["id"] = gw_host_id
        #         logger.info(f"Host object {host_object['name']} created successfully.")
        #         logger.info(f"Host object ID: {gw_host_id}")
        #     else:
        #         logger.info(f"Failed to create host object {host_object['name']}. Status code: {response_post.status_code}")
        #         return False

        #     # Get any IPv4 object ID
        #     response_get = requests.get(fmc_obj_network_url, headers=rest_api_headers, verify=False)
        #     response_get.raise_for_status()
        #     obj_networks_all = response_get.json().get('items', [])

        #     for obj in obj_networks_all:
        #         if obj['name'] == 'any-ipv4':
        #             any_ipv4_id = obj['id']

        #     static_route_payload["selectedNetworks"][0]["id"] = any_ipv4_id
        #     # Create route
        #     response_route = requests.post(fmc_routing_url.format(primary_status_id=primary_status_id), headers=rest_api_headers, data=json.dumps(static_route_payload), verify=False)
        #     response_route.raise_for_status()

        #     if response_route.status_code in [200, 201]:
        #         route_response = response_route.json()
        #         logger.info(f"Static route '{static_route_payload['name']}' created successfully.")
        #         logger.info(f"Route ID: {route_response.get('id')}")
        #     else:
        #         logger.info(f"Failed to create static route. Status code: {response_route.status_code}")
        #         return False
            # Configured Stanby IP for HA
            # time.sleep(5)
            ha_monitored_int_json_dict = {}
            response_ha_monitored_int = requests.get(ha_monitored_interfaces.format(ha_id=ha_id), headers=rest_api_headers, verify=False)
            response_ha_monitored_int.raise_for_status()        
            ha_monitored_int_json = response_ha_monitored_int.json().get('items', [])
            for monitored in ha_monitored_int_json:
                name = monitored.get('name')
                interface_id_ha_monitored = monitored.get('id')
                ha_monitored_int_json_dict[interface_id_ha_monitored] = name
            logger.info("HA Monitored Interfaces:")
            logger.info(ha_monitored_int_json_dict)

            for ifname in self.fmc_int_settings.values():
                if ifname ['ifname'] in ha_monitored_int_json_dict.values():
                    for interface_id, interface_name in ha_monitored_int_json_dict.items():
                        if interface_name == ifname['ifname']:
                            response_ha_monitored_int_detail = requests.get(ha_monitored_interfaces_detail.format(ha_id=ha_id,matching_interface_id=interface_id), headers=rest_api_headers, verify=False)
                            response_ha_monitored_int_detail.raise_for_status()
                            ha_monitored_int_detail_json = response_ha_monitored_int_detail.json()
                            logger.info(ha_monitored_int_detail_json)
                            int_name = ha_monitored_int_detail_json.get('name')
                            if int_name in self.fmc_ha_standby_settings['standby_ips'] and 'ipv4Configuration' in ha_monitored_int_detail_json:
                                standby_ip = self.fmc_ha_standby_settings['standby_ips'][int_name]
                                ha_monitored_int_detail_json.pop("links", None)
                                ha_monitored_int_detail_json.pop("metadata", None)
                                ha_monitored_int_detail_json['ipv4Configuration']['standbyIPv4Address'] = standby_ip
                                response_put = requests.put(ha_monitored_interfaces_detail.format(ha_id=ha_id, matching_interface_id=interface_id), headers=rest_api_headers, data=json.dumps(ha_monitored_int_detail_json), verify=False)
                                if response_put.status_code in [200, 201]:
                                    logger.info(f'Standby IP {standby_ip} configured successfully for interface {int_name}')
                                else:
                                    logger.error(f' Failed to configure standby IP for {standby_ip}. Status: {response_put.status_code}')
                                    logger.error(response_put.text)
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