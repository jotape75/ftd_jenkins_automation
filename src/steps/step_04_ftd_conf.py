"""
Step 4: FTD Network Configuration and Policy Assignment

Configures comprehensive network settings for Cisco FTD devices including network objects,
security zones, interfaces, routing, NAT policies, and platform settings assignment.

Key Features:
- Network object and security zone creation with conflict detection
- Interface configuration with IP addresses and HA standby IPs  
- Static route creation and NAT policy assignment
- Platform settings policy assignment with PUT/POST logic
- HA-aware configuration targeting primary device
- Email report integration for deployment tracking
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

        # These become INSTANCE VARIABLES - accessible to ALL methods
        self.fmc_ip = None
        self.rest_api_headers = None
        self.zones_id_list = []
        self.zones_id_dict = {}
        self.ha_id = None
        self.primary_device_id = None
        self.primary_status_id = None
        self.gw_host_id = None
        self.network_objects_id = {}
        # Templates that will be loaded later
        self.ftd_ha_tmp = None
        self.ftd_sec_zones_tmp = None
        self.fmc_int_settings = None
        self.fmc_route_settings = None
        self.fmc_ha_standby_settings = None


    def _initialize_api_urls(self):

        """Initialize API URLs after fmc_ip is set"""

        self.fmc_url_devices_int_detail = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/physicalinterfaces/{{interface_id}}"
        self.fmc_ha_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs"
        self.fmc_ha_check_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}"
        self.url_devices_int = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/physicalinterfaces"
        self.fmc_obj_host_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/hosts"
        self.fmc_obj_net_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/networks?bulk=true"
        self.fmc_obj_network_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/networks?expanded=true"
        self.fmc_routing_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devices/devicerecords/{{primary_status_id}}/routing/ipv4staticroutes"
        self.ha_monitored_interfaces = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}/monitoredinterfaces"
        self.ha_monitored_interfaces_detail = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/devicehapairs/ftddevicehapairs/{{ha_id}}/monitoredinterfaces/{{matching_interface_id}}"
        self.fmc_sec_zones_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/object/securityzones"
        self.fmc_nat_policy_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/policy/ftdnatpolicies"
        self.fmc_nat_rule_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/policy/ftdnatpolicies/{{nat_policy_id}}/autonatrules"
        self.fmc_policy_assignment_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/assignment/policyassignments"
        self.fmc_platform_settings_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/policy/ftdplatformsettingspolicies"
        self.fmc_policy_assignment_length_url = f"https://{self.fmc_ip}/api/fmc_config/v1/domain/default/assignment/policyassignments/{{pa_assignment_id}}"
    def load_devices_templates(self):
        from utils_ftd import FTD_HA_TEMPLATE, \
            FTD_SEC_ZONES_TEMPLATE, \
            FTD_INT_TEMPLATE, \
            FTD_STATIC_ROUTE_TEMPLATE, \
            FTD_HA_STANDBY_TEMPLATE, \
            FTD_NAT_TEMPLATE, \
            FTD_OBJECTS_TEMPLATE, \
            FTD_POLICY_ASSIGNMENT_TEMPLATE, \
            EMAIL_REPORT_DATA_FILE

        with open(FTD_HA_TEMPLATE, 'r') as f0, \
            open(FTD_SEC_ZONES_TEMPLATE, 'r') as f1, \
            open(FTD_INT_TEMPLATE, 'r') as f2, \
            open(FTD_STATIC_ROUTE_TEMPLATE, 'r') as f3, \
            open(FTD_HA_STANDBY_TEMPLATE, 'r') as f4, \
            open(FTD_NAT_TEMPLATE, 'r') as f5, \
            open(FTD_OBJECTS_TEMPLATE, 'r') as f6, \
            open(FTD_POLICY_ASSIGNMENT_TEMPLATE, 'r') as f7, \
            open(EMAIL_REPORT_DATA_FILE, 'r') as f8:

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
            self.ftd_nat_tmp = json.load(f5)
            logger.info("Loaded FTD NAT configuration template")
            self.fmc_obj_settings = json.load(f6)
            logger.info("Loaded FTD Objects configuration template")
            self.fmc_policy_assignment = json.load(f7)
            logger.info("Loaded FTD Policy Assignment configuration template")
            self.email_report_data = json.load(f8)
            logger.info("Loaded email report data dictionary")
            
    def save_report_data_file(self):
        from utils_ftd import EMAIL_REPORT_DATA_FILE

         # Save email report data dictionary to JSON file
        with open(EMAIL_REPORT_DATA_FILE, 'w') as f:
            json.dump(self.email_report_data, f, indent=4)

    def create_objects(self):
        try:
            host_object = self.fmc_obj_settings["host_object"]
            network_objects = self.fmc_obj_settings["network_object"]
            report_data = self.email_report_data.get("network_objects", [])

            # Get existing network objects
            response_get = requests.get(self.fmc_obj_network_url, headers=self.rest_api_headers, verify=False)
            response_get.raise_for_status()
            existing_network_objects = response_get.json().get('items', [])
            
            # Add this line to get existing host objects
            response_host_get = requests.get(self.fmc_obj_host_url + "?expanded=true", headers=self.rest_api_headers, verify=False)
            response_host_get.raise_for_status()
            existing_host_objects = response_host_get.json().get('items', [])
            
            # Combine both lists for conflict checking
            all_existing_objects = existing_network_objects + existing_host_objects
            
            # Check for conflicts before creating
            conflicts_found = False
            host_exists = False
            networks_exist = {}
        
            # Change this line to use combined list
            for obj in all_existing_objects:
                obj_name = obj.get("name")
                obj_value = obj.get("value")
                
                # Check for CONFLICTS in host object
                if obj_name == host_object['name'] and obj_value != host_object['value']:
                    logger.error(f"CONFLICT: Host object name '{host_object['name']}' exists but with different value. Existing: {obj_value}, Template: {host_object['value']}")
                    conflicts_found = True
                elif obj_value == host_object['value'] and obj_name != host_object['name']:
                    logger.error(f"CONFLICT: Host value '{host_object['value']}' exists but with different name. Existing: {obj_name}, Template: {host_object['name']}")
                    conflicts_found = True
                elif obj_name == host_object['name'] and obj_value == host_object['value']:
                    logger.info(f"Host object {host_object['name']} ({host_object['value']}) already exists - exact match.")
                    host_exists = True
                
                # Check for CONFLICTS in network objects (loop through the list)
                for template_net in network_objects:
                    if obj_name == template_net['name'] and obj_value != template_net['value']:
                        logger.error(f"CONFLICT: Network object name '{template_net['name']}' exists but with different value. Existing: {obj_value}, Template: {template_net['value']}")
                        conflicts_found = True
                    elif obj_value == template_net['value'] and obj_name != template_net['name']:
                        logger.error(f"CONFLICT: Network value '{template_net['value']}' exists but with different name. Existing: {obj_name}, Template: {template_net['name']}")
                        conflicts_found = True
                    elif obj_name == template_net['name'] and obj_value == template_net['value']:
                        logger.info(f"Network object {template_net['name']} ({template_net['value']}) already exists - exact match.")
                        networks_exist[template_net['name']] = True

            # Stop if conflicts found
            if conflicts_found:
                logger.error("Object conflicts detected. Cannot proceed with automation.")
                return False
            
            # Check if all networks exist
            all_networks_exist = len(networks_exist) == len(network_objects)
            
            # Skip creation if exact matches found
            if host_exists and all_networks_exist:
                logger.info("All objects already exist with exact matches. Skipping creation.")
                # Get existing host ID for later use
                for obj in existing_host_objects:
                    if obj.get('name') == host_object['name']:
                        self.gw_host_id = obj.get('id')
                        report_data.append({
                            "name": host_object['name'],
                            "IP": host_object['value'],
                            "type": "Host", 
                            "id": self.gw_host_id,
                            "status": "existing"
                        })
                        break
                
                # Get existing network object IDs for later use
                for obj in existing_network_objects:
                    for template_net in network_objects:
                        if obj.get('name') == template_net['name']:
                            self.network_objects_id[obj.get('name')] = obj.get('id')
                            report_data.append({
                                "name": obj.get('name'),
                                "IP": obj.get('value'),
                                "type": "Network",
                                "id": obj.get('id'),
                                "status": "existing"
                            })
                
                return True
            
            # Create host object if it doesn't exist
            if not host_exists:
                logger.info(f"Creating host object: {host_object['name']} - {host_object['value']}")
                response_post = requests.post(self.fmc_obj_host_url, headers=self.rest_api_headers, data=json.dumps(host_object), verify=False)
                obj_creation_re = response_post.json()
                
                if response_post.status_code in [200, 201]:
                    self.gw_host_id = obj_creation_re.get('id')
                    report_data.append({
                        "name": host_object['name'],
                        "IP": host_object['value'],
                        "type": "Host", 
                        "id": self.gw_host_id,
                        "status": "created"
                    })
                    logger.info(f"Host object {host_object['name']} - {host_object['value']} created with ID: {self.gw_host_id}.")
                else:
                    logger.error(f"Failed to create host object {host_object['name']}. Status code: {response_post.status_code}")
                    logger.error(response_post.text)
                    return False
            else:
                # Get existing host ID for later use
                for obj in existing_host_objects:
                    if obj.get('name') == host_object['name']:
                        self.gw_host_id = obj.get('id')
                        report_data.append({
                            "name": host_object['name'],
                            "IP": host_object['value'],
                            "type": "Host", 
                            "id": self.gw_host_id,
                            "status": "existing"
                        })
                        break
            
            # Create network objects if they don't exist
            if not all_networks_exist:
                # Create network objects that don't exist
                networks_to_create = []
                for template_net in network_objects:
                    if template_net['name'] not in networks_exist:
                        networks_to_create.append(template_net)
                
                if networks_to_create:
                    logger.info(f"Creating {len(networks_to_create)} network objects")
                   
                    response_post = requests.post(self.fmc_obj_net_url, headers=self.rest_api_headers, data=json.dumps(networks_to_create), verify=False)
                    net_obj_creation_re = response_post.json()
                    
                    if response_post.status_code in [200, 201]:
                        items = net_obj_creation_re.get('items', [])
                        for item in items:
                            self.network_objects_id[item['name']] = item['id']
                            logger.info(f"Network object {item['name']} - {item['value']} created with ID: {item['id']}")
                            report_data.append({
                                "name": item['name'],
                                "IP": item['value'],
                                "type": "Network",
                                "id": item['id'],
                                "status": "created"
                            })
                    else:
                        logger.error(f"Failed to create network objects. Status code: {response_post.status_code}")
                        logger.error(response_post.text)
                        return False

            # ALWAYS populate network object IDs for existing objects
            for obj in existing_network_objects:
                for template_net in network_objects:
                    if obj.get('name') == template_net['name']:
                        self.network_objects_id[obj.get('name')] = obj.get('id')
                        report_data.append({
                            "name": obj.get('name'),
                            "IP": obj.get('value'),
                            "type": "Network",
                            "id": obj.get('id'),
                            "status": "existing"
                        })
            
            self.save_report_data_file()
            logger.info("Email report data file updated with host and network objects.")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in create_objects: {e}")
            logger.error(f"network_objects structure: {network_objects}")
            return False
  
    def create_security_zones(self):

         # CREATE SECURITY ZONES ###
        report_data = self.email_report_data.get("security_zones", [])

        try:
            self.zones_id_list = []
            self.zones_id_dict = {}
            get_zones = requests.get(self.fmc_sec_zones_url, headers=self.rest_api_headers, verify=False)
            get_zones.raise_for_status()
            existing_zones = get_zones.json().get('items', [])
            existing_zone_names = [zone.get('name') for zone in existing_zones]

            for template_zone in self.ftd_sec_zones_tmp["sec_zones_payload"]:
                zone_name = template_zone.get('name')
                if zone_name not in existing_zone_names:
                    response_zones = requests.post(self.fmc_sec_zones_url, headers=self.rest_api_headers, data=json.dumps(template_zone), verify=False)
                    zones = response_zones.json()
                    zones_id = zones.get('id')
                    self.zones_id_list.append(zones_id)
                    self.zones_id_dict[zone_name] = zones_id
                    if response_zones.status_code in [200, 201]:
                        logger.info(f"Security zone {zone_name} created successfully.")
                        report_data.append({
                        "name": zones.get('name'),
                        "type": "Security Zone",
                        "id": zones.get('id'),
                        "status": "created"
                    })
                    else:
                        logger.info(f"Failed to create security zone {zone_name}. Status code: {response_zones.status_code}")
                        logger.info(response_zones.text)
                        return False
                else:
                    # Security zone already exists, retrieve its ID
                    for existing_zone in existing_zones:
                        if existing_zone.get('name') == zone_name:
                            self.zones_id_list.append(existing_zone.get('id'))
                            self.zones_id_dict[zone_name] = existing_zone.get('id')
                            logger.info(f"Security zone {zone_name} already exists. Skipping creation.")
                            report_data.append({
                               "name": existing_zone.get('name'),
                               "type": "Security Zone",
                               "id": existing_zone.get('id'),
                               "status": "existing"
                            })
                            break
            self.save_report_data_file()
            logger.info("Email report data file updated with host and network objects.")
            time.sleep(5)
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
    def configure_interfaces(self):

     ### CONFIGURE INTERFACES ###
        interfaces_configured = self.email_report_data.get("interfaces_configured", [])
        try:
        # Get the HA primary device ID
            def configure_interface(
                interface_id,
                interface_name,
                config,  # dict from your external config, includes zone_index
                zones_id_list,
                primary_status_id,
                primary_name,
                headers
            ):
                """
                Helper to configure a single interface on the FMC device using external config.
                """

                response_int = requests.get(self.fmc_url_devices_int_detail.format(primary_status_id=primary_status_id,interface_id=interface_id), headers=headers, verify=False)
                response_int.raise_for_status()
                interface_obj = response_int.json()
                interface_obj.pop("links", None)
                interface_obj.pop("metadata", None)
                # Use zone_index from config to select the correct security zone
                zone_index = config["zone_index"]
                interface_obj["securityZone"] = {
                    "id": zones_id_list[zone_index],
                    "type": "SecurityZone"
                }
                interface_obj["ifname"] = config["ifname"]
                interface_obj["enabled"] = True
                interface_obj["ipv4"] = {
                    "static": {
                        "address": config["ip_address"],
                        "netmask": config["netmask"]
                    }
                }
                response_put = requests.put(self.fmc_url_devices_int_detail.format(primary_status_id=primary_status_id,interface_id=interface_id), headers=headers, data=json.dumps(interface_obj), verify=False)
                if response_put.status_code in [200, 201]:
                    logger.info(f"Security zone assigned to interface {interface_name} on device {primary_name} successfully.")
                    logger.info(f'IP address assigned to interface {interface_name} on device {primary_name} successfully.')
                    interfaces_configured.append({
                        "ifname": config["ifname"],
                        "ip_address": config["ip_address"],
                        "netmask": config["netmask"],
                        "id": interface_id,
                        "status": "created"
                    })
                else:
                    logger.info(f"Failed to assign security zone to interface {interface_name} on device {primary_name}. Status code: {response_put.status_code}")
                    logger.info(response_put.text)
             
            #GET HA ID
            response_ha_id = requests.get(self.fmc_ha_settings_url, headers=self.rest_api_headers, verify=False)
            response_ha_id.raise_for_status()
            ha_output = response_ha_id.json().get('items', [])
            self.ha_id = ""
            for ha in ha_output:
                if ha.get('name') == self.ftd_ha_tmp['ha_payload']['name']:
                    self.ha_id = ha.get("id")
                    break
            response_ha_check = requests.get(self.fmc_ha_check_url.format(ha_id=self.ha_id), headers=self.rest_api_headers, verify=False)
            response_ha_check.raise_for_status()
            ha_json = response_ha_check.json()
            logger.info(f'Active device is {ha_json["metadata"]["primaryStatus"]["device"]["name"]}')
            logger.info(response_ha_check.text)
            self.primary_status_id = ha_json["metadata"]["primaryStatus"]["device"]["id"]
            primary_name = ha_json["metadata"]["primaryStatus"]["device"]["name"]
            response_int_check = requests.get(self.url_devices_int.format(primary_status_id=self.primary_status_id), headers=self.rest_api_headers, verify=False)
            response_int_check.raise_for_status()
            interfaces = response_int_check.json().get('items', [])

            for int_id in interfaces:
                int_name = int_id['name']
                if int_name  in self.fmc_int_settings:
                    config = self.fmc_int_settings[int_name]
                    configure_interface(
                        interface_id=int_id['id'],
                        interface_name=int_name,
                        config=config,
                        zones_id_list=self.zones_id_list,
                        primary_status_id=self.primary_status_id,
                        primary_name=primary_name,
                        headers=self.rest_api_headers
                    )
            self.save_report_data_file()
            time.sleep(15)
            
            # Return True after all interfaces are processed
            logger.info("All interfaces configured successfully.")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
        
    def create_default_route(self):

       ## CREATE DEFAULT ROUTE ###
        static_routes = self.email_report_data.get("static_routes", [])
        GW_OUTSIDE = f'{os.getenv("FW_HOSTNAME_01", "")}_HA_outside_gw'

        try:
            static_route_payload = self.fmc_route_settings["static_route_payload"]

            # Get any IPv4 object ID
            static_route_payload["gateway"]["object"]["id"] = self.gw_host_id
            response_get = requests.get(self.fmc_obj_network_url, headers=self.rest_api_headers, verify=False)
            response_get.raise_for_status()
            obj_networks_all = response_get.json().get('items', [])
            
            any_ipv4_id = None
            any_ipv4_name = None
            for obj in obj_networks_all:
                if obj['name'] == 'any-ipv4':
                    any_ipv4_id = obj['id']
                    # any_ipv4_name = obj['name']
                    break
            static_route_payload["selectedNetworks"][0]["id"] = any_ipv4_id
            # Create route
            response_route = requests.post(self.fmc_routing_url.format(primary_status_id=self.primary_status_id), headers=self.rest_api_headers, data=json.dumps(static_route_payload), verify=False)

            if response_route.status_code in [200, 201]:
                route_response = response_route.json()
                logger.info(f"Static route '{static_route_payload['name']}' created successfully.")
                logger.info(f"Route ID: {route_response.get('id')}")
                static_routes.append({
                    "name": static_route_payload.get('name', 'default_route'),  # Use template name
                    "source": any_ipv4_name or 'any-ipv4',  # Safe fallback
                    "next_hop": GW_OUTSIDE,
                    "type": "Static Route",
                    "id": route_response.get('id'),
                    "status": "created"
                })
                self.save_report_data_file()
                logger.info("Email report data file updated with static route.")
                return True
            else:
                logger.info(f"Failed to create static route. Status code: {response_route.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
        
    def configure_ha_standby(self):

        interfaces_configured = self.email_report_data.get("interfaces_configured", [])
        try:
            # Configured Standby IP for HA
            time.sleep(5)
            ha_monitored_int_json_dict = {}
            response_ha_monitored_int = requests.get(self.ha_monitored_interfaces.format(ha_id=self.ha_id), headers=self.rest_api_headers, verify=False)
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
                            response_ha_monitored_int_detail = requests.get(self.ha_monitored_interfaces_detail.format(ha_id=self.ha_id, matching_interface_id=interface_id), headers=self.rest_api_headers, verify=False)
                            response_ha_monitored_int_detail.raise_for_status()
                            ha_monitored_int_detail_json = response_ha_monitored_int_detail.json()
                            logger.info(ha_monitored_int_detail_json)
                            int_name = ha_monitored_int_detail_json.get('name')
                            if int_name in self.fmc_ha_standby_settings['standby_ips'] and 'ipv4Configuration' in ha_monitored_int_detail_json:
                                standby_ip = self.fmc_ha_standby_settings['standby_ips'][int_name]
                                ha_monitored_int_detail_json.pop("links", None)
                                ha_monitored_int_detail_json.pop("metadata", None)
                                ha_monitored_int_detail_json['ipv4Configuration']['standbyIPv4Address'] = standby_ip
                                response_put = requests.put(self.ha_monitored_interfaces_detail.format(ha_id=self.ha_id, matching_interface_id=interface_id), headers=self.rest_api_headers, data=json.dumps(ha_monitored_int_detail_json), verify=False)
                                if response_put.status_code in [200, 201]:
                                    logger.info(f'Standby IP {standby_ip} configured successfully for interface {int_name}')
                                    for interface in interfaces_configured:
                                        if interface['ifname'] == int_name:
                                            interface['standby_ip'] = standby_ip
                                            break
                                else:
                                    logger.error(f' Failed to configure standby IP for {standby_ip}. Status: {response_put.status_code}')
                                    logger.error(response_put.text)
                                    return False
            # Return True after all interfaces are processed
            logger.info(f"HA standby IP configuration completed successfully.")
            self.save_report_data_file()
            logger.info("Email report data file updated with standby IPs.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
    def configure_NAT(self):
        # Create NAT policy
        nat_policy_report = self.email_report_data.get("nat_policy", [])
        nat_rules_report = self.email_report_data.get("nat_rules", [])
        try:
            nat_policy = self.ftd_nat_tmp["nat_policy"]
            nat_rule = self.ftd_nat_tmp["nat_rule"]
        
            response_nat = requests.post(self.fmc_nat_policy_url, headers=self.rest_api_headers, data=json.dumps(nat_policy), verify=False)
            if response_nat.status_code in [200, 201]:
                nat_response = response_nat.json()
                nat_policy_name = nat_response.get('name')
                logger.info(f"NAT policy '{nat_policy_name}' created successfully.")
                nat_policy_id = nat_response.get('id')
                logger.info(f"NAT Policy ID: {nat_policy_id}")
                nat_policy_report.append({
                    "name": nat_policy_name,
                    "type": "NAT Policy",
                    "id": nat_policy_id,
                    "status": "created"
                })
                self.save_report_data_file()
                logger.info("Email report data file updated with NAT policy.")
            
                # Create NAT rule
                # Update network object IDs in NAT rule
                INSIDE_NET_NAME = f'INSIDE_NET_{os.getenv("FW_HOSTNAME_01", "")}_HA'
                OUTSIDE_SEC_ZONE_NAME = os.getenv('OUTSIDE_SEC_ZONE', '')
                INSIDE_SEC_ZONE_NAME = os.getenv('INSIDE_SEC_ZONE', '')

                if INSIDE_NET_NAME in self.network_objects_id:
                    nat_rule["originalNetwork"]["id"] = self.network_objects_id.get(INSIDE_NET_NAME)
                if INSIDE_SEC_ZONE_NAME in self.zones_id_dict:
                    nat_rule["sourceInterface"]["id"] = self.zones_id_dict.get(INSIDE_SEC_ZONE_NAME)
                if OUTSIDE_SEC_ZONE_NAME in self.zones_id_dict:
                    nat_rule["destinationInterface"]["id"] = self.zones_id_dict.get(OUTSIDE_SEC_ZONE_NAME)

                response_nat_rule = requests.post(self.fmc_nat_rule_url.format(nat_policy_id=nat_policy_id), headers=self.rest_api_headers, data=json.dumps(nat_rule), verify=False)
                if response_nat_rule.status_code in [200, 201]:
                    nat_rule_response = response_nat_rule.json()
                    nat_rule_id = nat_rule_response.get('id')
                    nat_rules_report.append({
                            "name": nat_rule_response.get('name'),
                            "type": nat_rule_response.get('natType'),
                            "id": nat_rule_id,
                            "source_interface": INSIDE_SEC_ZONE_NAME,
                            "destination_interface": OUTSIDE_SEC_ZONE_NAME,
                            "original_network": INSIDE_NET_NAME,
                            "status": "created"
                        })
                    logger.info(f"NAT rule created successfully - ID: {nat_rule_id}")
                    self.save_report_data_file()
                    logger.info("Email report data file updated with NAT rule.")
                    nat_policy_assignment = self.fmc_policy_assignment["nat_policy_assignment"]
                    nat_policy_assignment["policy"]["name"] = nat_policy_name
                    nat_policy_assignment["policy"]["id"] = nat_policy_id
                    nat_policy_assignment["targets"][0]["name"] = self.ftd_ha_tmp['ha_payload']['name']
                    nat_policy_assignment["targets"][0]["id"] = self.primary_status_id
                    response_policy_assignment = requests.post(self.fmc_policy_assignment_url, headers=self.rest_api_headers, data=json.dumps(nat_policy_assignment), verify=False)
                    if response_policy_assignment.status_code in [200, 201]:
                        logger.info(f"NAT policy '{nat_policy_name}' assigned to device {self.ftd_ha_tmp['ha_payload']['name']} successfully.")
                        return True
                    else:
                        logger.error(f"Failed to assign NAT policy. Status: {response_policy_assignment.status_code}")
                        logger.error(response_policy_assignment.text)
                        return False
                else:
                    logger.error(f"Failed to create NAT rule. Status: {response_nat_rule.status_code}")
                    return False
            else:
                logger.error(f"Failed to create NAT policy. Status: {response_nat.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False
    def platform_settings_assignment(self):
        # Assign platform settings to device
        platform_settings = self.fmc_policy_assignment["psettings_policy_assignment"]
        platform_settings_update = self.fmc_policy_assignment["psettings_policy_assignment_update"]
        psettings_report = self.email_report_data.get("platform_settings", [])
        try:
            response_platform_settings = requests.get(self.fmc_platform_settings_url, headers=self.rest_api_headers, verify=False)
            response_platform_settings.raise_for_status()
            platform_settings_list = response_platform_settings.json().get('items', [])
            platform_settings_id = None
            platform_settings_name = None
            for setting in platform_settings_list:
                if setting.get('name') == platform_settings["policy"]["name"]:
                    platform_settings_id = setting.get('id')
                    platform_settings_name = setting.get('name')
                    break
            response_get_policy_assignment = requests.get(self.fmc_policy_assignment_url, headers=self.rest_api_headers, verify=False)
            response_get_policy_assignment.raise_for_status()
            existing_policy_assignments = response_get_policy_assignment.json().get('items', [])
            for name in existing_policy_assignments:
                if name.get('name') == platform_settings_name:
                    pa_assignment_id = name.get('id')
                    response_pa_length = requests.get(self.fmc_policy_assignment_length_url.format(pa_assignment_id=pa_assignment_id), headers=self.rest_api_headers, verify=False)
                    response_pa_length.raise_for_status()
                    psettings_length = response_pa_length.json()
                    existing_targets = psettings_length.get('targets', [])
                    pa_length = len(existing_targets)

                    new_target = {
                        "id": self.primary_status_id,
                        "type": "Device",
                        "name": self.ftd_ha_tmp['ha_payload']['name']
                    }
                    existing_targets.append(new_target)

                    logger.info(f"Policy assignment '{platform_settings_name}' exists with {pa_length} target(s).")
                    if pa_length > 0:
                        platform_settings_update["id"] = pa_assignment_id
                        platform_settings_update["policy"]["name"] = platform_settings_name
                        platform_settings_update["policy"]["id"] = platform_settings_id
                        platform_settings_update["targets"]= existing_targets

                        response_pa_length = requests.put(self.fmc_policy_assignment_length_url.format(pa_assignment_id=pa_assignment_id), headers=self.rest_api_headers, data=json.dumps(platform_settings_update), verify=False)
                        if response_pa_length.status_code in [200, 201]:
                            logger.info(f"Platform settings '{platform_settings_name}' assigned to device {self.ftd_ha_tmp['ha_payload']['name']} successfully.")
                            psettings_report.append({
                                "name": platform_settings_name,
                                "id": platform_settings_id,
                                "type": "Platform Settings",
                                    "status": "assigned"
                            })
                            self.save_report_data_file()
                            logger.info("Email report data file updated with platform settings assignment.")
                            return True
                        else:
                            logger.error(f"Failed to assign Platform settings. Status: {response_pa_length.status_code}")
                            logger.error(response_pa_length.text)
                            return False
                else:
                    platform_settings["targets"][0]["name"] = self.ftd_ha_tmp['ha_payload']['name']
                    platform_settings["policy"]["name"] = platform_settings_name
                    platform_settings["policy"]["id"] = platform_settings_id
                    platform_settings["targets"][0]["id"] = self.primary_status_id
                    response_policy_assignment = requests.post(self.fmc_policy_assignment_url, headers=self.rest_api_headers, data=json.dumps(platform_settings), verify=False)
                    if response_policy_assignment.status_code in [200, 201]:
                        logger.info(f"Platform settings '{platform_settings_name}' assigned to device {self.ftd_ha_tmp['ha_payload']['name']} successfully.")
                        psettings_report.append({
                            "name": platform_settings_name,
                            "id": platform_settings_id,
                            "type": "Platform Settings",
                            "status": "assigned"
                        })
                        self.save_report_data_file()
                        logger.info("Email report data file updated with platform settings assignment.")
                        return True
                    else:
                        logger.error(f"Failed to assign Platform settings. Status: {response_policy_assignment.status_code}")
                        logger.error(response_policy_assignment.text)
                        return False
                        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return False

    def execute(self):
        """
        Execute comprehensive FTD network configuration with FMC.
        
        Configures network objects, security zones, interfaces with HA standby IPs,
        routing, NAT policies, and platform settings via REST API.
        
        Returns:
            bool: True if all configuration steps successful, False otherwise
        """
        try:
            self.load_devices_templates()
            self.fmc_ip = os.getenv('FMC_IP')
            self._initialize_api_urls()

            with open('api_keys_data.pkl', 'rb') as f:
                self.rest_api_headers = pickle.load(f)
            
            # Check each step and return False immediately if any fails
            if not self.create_objects():
                logger.error("Failed to create objects")
                return False
                
            if not self.create_security_zones():
                logger.error("Failed to create security zones")
                return False
            if not self.configure_interfaces():
                logger.error("Failed to configure interfaces")
                return False
                
            if not self.create_default_route():
                logger.error("Failed to create default route")
                return False
                
            if not self.configure_ha_standby():
                logger.error("Failed to configure HA standby")
                return False
                
            if not self.configure_NAT():
                logger.error("Failed to configure NAT")
                return False
            if not self.platform_settings_assignment():
                logger.error("Failed to assign platform settings")
                return False
            
             # All steps succeeded

            logger.info("FTD configuration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in FTD configuration: {e}")
            return False

    