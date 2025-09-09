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
        self.jenkins_params = self._get_jenkins_params()
    
    def _get_jenkins_params(self):
        """Get Jenkins parameters from environment variables"""
        return {
            # HA Interfaces
            'ha1_interface': os.getenv('HA1_INTERFACE', 'ethernet1/4'),
            'ha2_interface': os.getenv('HA2_INTERFACE', 'ethernet1/5'),
            
            # Data Interface IPs 
            'ethernet1_1_ip_trust': os.getenv('ETHERNET1_1_IP_TRUST', '10.10.10.5/24'),
            'ethernet1_2_ip_untrust': os.getenv('ETHERNET1_2_IP_UNTRUST', '200.200.200.2/24'),
            'ethernet1_3_ip_dmz': os.getenv('ETHERNET1_3_IP_DMZ', '10.30.30.5/24'),
            
            # Gateway/Routing
            'default_gateway': os.getenv('DEFAULT_GATEWAY', '200.200.200.1'),
            'static_route_network': os.getenv('STATIC_ROUTE_NETWORK', '10.0.0.0/8'),
            'static_route_nexthop': os.getenv('STATIC_ROUTE_NEXTHOP', '10.10.10.1'),
            
            # NAT
            'source_nat_ip': os.getenv('SOURCE_NAT_IP', '200.200.200.10'),
            
            # Security Zones 
            'trust': os.getenv('TRUST', 'ethernet1/1'),
            'untrust': os.getenv('UNTRUST', 'ethernet1/2'),
            'dmz': os.getenv('DMZ', 'ethernet1/3')
        }
    
    def update_data_interface_template(self):
        """Update data interface template with Jenkins parameters"""
        template_file = f"{self.data_dir}/data_interface.xml"
        
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Replace placeholders with Jenkins environment variables
        content = content.replace('{ETHERNET1_1_IP_TRUST}', os.getenv('ETHERNET1_1_IP_TRUST', ''))
        content = content.replace('{ETHERNET1_2_IP_UNTRUST}', os.getenv('ETHERNET1_2_IP_UNTRUST', ''))
        content = content.replace('{ETHERNET1_3_IP_DMZ}', os.getenv('ETHERNET1_3_IP_DMZ', ''))

            
        with open(template_file, 'w') as f:
            f.write(content)
        
        logger.info("Updated data interface template with Jenkins parameters")
    
    def update_ha_interface_template(self):
        """
        HA interface template should NOT be updated here - 
        it needs dynamic IPs per device in step_03_ha_config.py
        """
        logger.info("HA interface template kept with placeholders for dynamic updates")
        # Don't update this template - leave {ha1_ip} as placeholder
        return
    
    def update_routing_template(self):
        """Update routing template with Jenkins parameters"""
        template_file = f"{self.data_dir}/static_route_template.xml"
        
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Replace placeholders with Jenkins environment variables 
        content = content.replace('{STATIC_ROUTE_NETWORK}', os.getenv('STATIC_ROUTE_NETWORK', '0.0.0.0/0'))
        content = content.replace('{STATIC_ROUTE_NEXTHOP}', os.getenv('STATIC_ROUTE_NEXTHOP', ''))
        content = content.replace('{untrust}', os.getenv('UNTRUST', 'ethernet1/2'))  
        
        with open(template_file, 'w') as f:
            f.write(content)
        
        logger.info("Updated routing template with Jenkins parameters")

    def update_nat_template(self):
        """Update NAT template with Jenkins parameters"""
        template_file = f"{self.data_dir}/source_nat_template.xml"
        
        with open(template_file, 'r') as f:
            content = f.read()
        
        content = content.replace('{ETHERNET1_2_IP_UNTRUST}', os.getenv('ETHERNET1_2_IP_UNTRUST', ''))  
        content = content.replace('{untrust}', os.getenv('UNTRUST', 'ethernet1/2'))  
        content = content.replace('{trust}', os.getenv('TRUST', 'ethernet1/1'))      
        content = content.replace('{dmz}', os.getenv('DMZ', 'ethernet1/3'))         
        
        with open(template_file, 'w') as f:
            f.write(content)
        
        logger.info("Updated NAT template with Jenkins parameters")
    
    def update_zones_template(self):
        """Update zones template with Jenkins parameters"""
        template_file = f"{self.data_dir}/zones.xml"
        
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Replace placeholders with Jenkins environment variables
        content = content.replace('{TRUST}', os.getenv('TRUST', ''))
        content = content.replace('{UNTRUST}', os.getenv('UNTRUST', ''))
        content = content.replace('{DMZ}', os.getenv('DMZ', ''))
        
        with open(template_file, 'w') as f:
            f.write(content)
        
        logger.info("Updated zones template with Jenkins parameters")
    
    def execute(self):
        """Execute all template updates"""
        try:
            logger.info("Starting template updates with Jenkins parameters...")
            logger.info(f"Parameters: {self.jenkins_params}")
            
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Update all templates
            self.update_data_interface_template()
            self.update_ha_interface_template() 
            self.update_routing_template()
            self.update_nat_template()
            self.update_zones_template()
            
            logger.info("All templates updated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error updating templates: {e}")
            return False

if __name__ == "__main__":
    updater = TemplateUpdater()
    success = updater.execute()
    sys.exit(0 if success else 1)