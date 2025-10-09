#!/usr/bin/env python3
"""
Update XML templates with Jenkins parameter values

Pre-processes configuration templates by replacing placeholders with values
from Jenkins form parameters. Prepares templates for firewall configuration
steps while maintaining dynamic placeholders where needed.

Key Features:
- Loads parameters from Jenkins environment variables
- Updates data interface, routing, NAT, and zones templates
- Preserves HA template placeholders for per-device configuration
- Handles both static values and dynamic interface assignments
- Validates template updates with comprehensive error handling
"""

import os
import sys
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class TemplateUpdater:
    """
    Updates XML templates with Jenkins parameter values
    """
    
    def __init__(self):
        self.data_dir = "data/payload"
        
    def update_devices_template(self):
        """Update fmc_devices template with Jenkins parameters"""
        template_file = f"{self.data_dir}/fmc_devices.json"

        with open(template_file, 'r') as f:
            content = f.read()
        
        # Replace placeholders with Jenkins environment variables
        content = content.replace('{IP_ADD_FW_01}', os.getenv('IP_ADD_FW_01', ''))
        content = content.replace('{IP_ADD_FW_02}', os.getenv('IP_ADD_FW_02', ''))
        content = content.replace('{FW_HOSTNAME_01}', os.getenv('FW_HOSTNAME_01', ''))
        content = content.replace('{FW_HOSTNAME_02}', os.getenv('FW_HOSTNAME_02', ''))
        content = content.replace('{REGKEY}', os.getenv('REGKEY', ''))

        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("Updated fmc_devices template with Jenkins parameters")

    def update_ftd_ha_payload(self):
        """Update ftd_ha_payload template with Jenkins parameters"""
        template_file = f"{self.data_dir}/fmc_ha_payload.json"

        with open(template_file, 'r') as f:
            content = f.read()

        # Replace placeholders with Jenkins environment variables
        HA_NAME = f'{os.getenv("FW_HOSTNAME_01", "")}_HA'
        content = content.replace('{HA_NAME}', HA_NAME)
        content = content.replace('{HA_INTERFACE}', os.getenv('HA_INTERFACE', ''))

        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("Updated ftd_ha_payload with Jenkins parameters")

    def update_objects_template(self):
        """Update default route template with Jenkins parameters"""
        GW_OUTSIDE = f'{os.getenv("FW_HOSTNAME_01", "")}_HA_outside_gw'
        INSIDE_NET_NAME = f'INSIDE_NET_{os.getenv("FW_HOSTNAME_01", "")}_HA'
        OUTSIDE_NET_NAME = f'OUTSIDE_NET_{os.getenv("FW_HOSTNAME_01", "")}_HA'
        DMZ_NET_NAME = f'DMZ_NET_{os.getenv("FW_HOSTNAME_01", "")}_HA'
        template_file = f"{self.data_dir}/objects.json"

        with open(template_file, 'r') as f:
            content = f.read()

        # Replace placeholders with Jenkins environment variables
        content = content.replace('{DEFAULT_ROUTE_GATEWAY}', os.getenv('DEFAULT_ROUTE_GATEWAY', ''))
        content = content.replace('{GW_OUTSIDE}', GW_OUTSIDE)
        content = content.replace('{INSIDE_NETWORK}', os.getenv('INSIDE_NETWORK', ''))
        content = content.replace('{INSIDE_NET_NAME}', INSIDE_NET_NAME)
        content = content.replace('{OUTSIDE_NETWORK}', os.getenv('OUTSIDE_NETWORK', ''))
        content = content.replace('{OUTSIDE_NET_NAME}', OUTSIDE_NET_NAME)
        content = content.replace('{DMZ_NETWORK}', os.getenv('DMZ_NETWORK', ''))
        content = content.replace('{DMZ_NET_NAME}', DMZ_NET_NAME)

        # Write back
        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("Updated objects template with Jenkins parameters")
    
    def update_sec_zones_template(self):
        """Update security zones template with Jenkins parameters"""
        template_file = f"{self.data_dir}/sec_zones.json"

        with open(template_file, 'r') as f:
            content = f.read()

        # Replace placeholders with Jenkins environment variables
        content = content.replace('{OUTSIDE_SEC_ZONE}', os.getenv('OUTSIDE_SEC_ZONE', ''))
        content = content.replace('{INSIDE_SEC_ZONE}', os.getenv('INSIDE_SEC_ZONE', ''))
        content = content.replace('{DMZ_SEC_ZONE}', os.getenv('DMZ_SEC_ZONE', ''))

        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("Updated security zones template with Jenkins parameters")      

    def update_interfaces_template(self):
        """Update interfaces template with Jenkins parameters"""
        template_file = f"{self.data_dir}/interface.json"

        with open(template_file, 'r') as f:
            content = f.read()

        # Replace placeholders with Jenkins environment variables
        content = content.replace('{INSIDE_INTERFACE}', os.getenv('INSIDE_INTERFACE', ''))
        content = content.replace('{INSIDE_INTERFACE_NAME}', os.getenv('INSIDE_INTERFACE_NAME', ''))
        content = content.replace('{OUTSIDE_INTERFACE}', os.getenv('OUTSIDE_INTERFACE', ''))
        content = content.replace('{OUTSIDE_INTERFACE_NAME}', os.getenv('OUTSIDE_INTERFACE_NAME', ''))
        content = content.replace('{DMZ_INTERFACE}', os.getenv('DMZ_INTERFACE', ''))
        content = content.replace('{DMZ_INTERFACE_NAME}', os.getenv('DMZ_INTERFACE_NAME', ''))
        content = content.replace('{INSIDE_IP}', os.getenv('INSIDE_IP', ''))
        content = content.replace('{INSIDE_MASK}', os.getenv('INSIDE_MASK', ''))
        content = content.replace('{OUTSIDE_IP}', os.getenv('OUTSIDE_IP', ''))
        content = content.replace('{OUTSIDE_MASK}', os.getenv('OUTSIDE_MASK', ''))
        content = content.replace('{DMZ_IP}', os.getenv('DMZ_IP', ''))
        content = content.replace('{DMZ_MASK}', os.getenv('DMZ_MASK', ''))

        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("Updated interfaces template with Jenkins parameters")

    def default_route_template(self):
        """Update default route template with Jenkins parameters"""
        GW_OUTSIDE = f'{os.getenv("FW_HOSTNAME_01", "")}_HA_outside_gw'
        template_file = f"{self.data_dir}/default_route.json"

        with open(template_file, 'r') as f:
            content = f.read()

        # Replace placeholders with Jenkins environment variables
        content = content.replace('{OUTSIDE_INTERFACE_NAME}', os.getenv('OUTSIDE_INTERFACE_NAME', ''))

        # Write back
        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("Updated default route template with Jenkins parameters")
    def update_ha_standby_template(self):

        """Update HA standby IP template with user inputs"""

        template_file = f"{self.data_dir}/ha_standby_ip.json"
        
        # Read template
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Replace placeholders
        content = content.replace('{OUTSIDE_STANDBY_IP}', os.getenv('OUTSIDE_STANDBY_IP', ''))
        content = content.replace('{INSIDE_STANDBY_IP}', os.getenv('INSIDE_STANDBY_IP', ''))
        content = content.replace('{DMZ_STANDBY_IP}', os.getenv('DMZ_STANDBY_IP', ''))

        # Write back
        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("HA standby IP template updated successfully")
    def update_NAT_template(self):

        """Update NAT template with Jenkins parameters"""

        NAME = f'NAT_Policy_{os.getenv("FW_HOSTNAME_01", "")}_HA'
        HA_NAME = f'{os.getenv("FW_HOSTNAME_01", "")}_HA'
        template_file = f"{self.data_dir}/nat.json"

        with open(template_file, 'r') as f:
            content = f.read()

        # Replace placeholders with Jenkins environment variables
        content = content.replace('{NAME}', NAME)
        content = content.replace('{HA_NAME}', HA_NAME)

        # Write back
        with open(template_file, 'w') as f:
            f.write(content)

        logger.info("Updated NAT template with Jenkins parameters")
        
    def execute(self):
        """Execute all template updates"""
        try:
            logger.info("Starting template updates with Jenkins parameters...")

            
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Update all templates
            self.update_devices_template()
            self.update_ftd_ha_payload() 
            self.update_objects_template()
            self.update_sec_zones_template()
            self.update_interfaces_template()
            self.default_route_template()
            self.update_ha_standby_template()
            self.update_NAT_template()
            
            logger.info("All templates updated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error updating templates: {e}")
            return False

if __name__ == "__main__":
    updater = TemplateUpdater()
    success = updater.execute()
    sys.exit(0 if success else 1)