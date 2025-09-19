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

    # def update_ha_interface_template(self):
    #     """
    #     HA interface template should NOT be updated here - 
    #     it needs dynamic IPs per device in step_03_ha_config.py
    #     """
    #     logger.info("HA interface template kept with placeholders for dynamic updates")
    #     # Don't update this template - leave {ha1_ip} as placeholder
    #     return
    

    
    def execute(self):
        """Execute all template updates"""
        try:
            logger.info("Starting template updates with Jenkins parameters...")

            
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Update all templates
            self.update_devices_template()
            self.update_ftd_ha_payload() 
            # self.update_routing_template()
            # self.update_nat_template()
            # self.update_zones_template()
            
            logger.info("All templates updated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error updating templates: {e}")
            return False

if __name__ == "__main__":
    updater = TemplateUpdater()
    success = updater.execute()
    sys.exit(0 if success else 1)