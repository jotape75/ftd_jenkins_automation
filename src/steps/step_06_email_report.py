"""
Step 6: EMAIL DEPLOYMENT REPORT

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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
import logging
import json
import sys
import os
# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step06_EMAIL_DEPLOYMENT_REPORT:
    """
    Generate and send email deployment reports.

    Uses credentials and device information from Jenkins form parameters.
    """
    
    def __init__(self):
        """
        Initialize email deployment report step.
        """
    def load_devices_templates(self):
        try:
            from utils_ftd import EMAIL_REPORT_DATA_FILE
            
            with open(EMAIL_REPORT_DATA_FILE, 'r') as f0:
                self.email_report_data = json.load(f0)
                logger.info("Loaded email report data dictionary")
        except FileNotFoundError:
            logger.warning("Email report data file not found, using empty data")
            self.email_report_data = {"health_status": [],
                                      "ha_status": [],
                                      "network_objects": [],
                                       "security_zones": [], 
                                       "interfaces_configured": [], 
                                       "static_routes": [],
                                       "access_policies": [],
                                       "nat_policy": [], 
                                       "nat_rules": [],
                                       "platform_settings": []}
        except Exception as e:
            logger.error(f"Error loading email report data: {e}")
            self.email_report_data = {"health_status": [],
                                       "ha_status": [],
                                       "network_objects": [],
                                       "security_zones": [],
                                       "interfaces_configured": [],
                                       "static_routes": [],
                                       "access_policies": [],
                                       "nat_policy": [], 
                                       "nat_rules": [],
                                       "platform_settings": []}
    def get_health_status_color(self, health):

        _yellow = 'color: #B8860B;'  # Dark goldenrod 
        _red = 'color: #DC143C;'  # Crimson 
        _blue = 'color: #0000CD;' # Medium blue

        if health in ['green']:
            return 'color: green;'
        elif health in ['yellow']:
            return _yellow
        elif health in ['red']:
            return _red
        elif health in ['recovered']:
            return _blue
        else:
            return 'color: black;'

    
    def _generate_report_body(self):
        """
        Generate the HTML body for the email report.
        """
        network_objects = self.email_report_data.get("network_objects", [])
        security_zones = self.email_report_data.get("security_zones", [])
        interfaces_configured = self.email_report_data.get("interfaces_configured", [])
        static_routes = self.email_report_data.get("static_routes", [])
        nat_rules = self.email_report_data.get("nat_rules", [])
        nat_policy = self.email_report_data.get("nat_policy", [])
        access_policies = self.email_report_data.get("access_policies", [])
        ha_status = self.email_report_data.get("ha_status", [])
        health_status = self.email_report_data.get("health_status", [])
        platform_settings = self.email_report_data.get("platform_settings", [])
        deployment_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate table for health status
        health_table = ""
        for health in health_status:
            health_table += f"""
            <tr>
                <td><strong>{health.get('device_name', 'N/A')}</strong></td>
                <td style="{self.get_health_status_color(health.get('health_status', 'N/A'))}; font-weight: bold;">{health.get('health_status', 'N/A')}</td>
                <td><strong>{health.get('deployment_status', 'N/A')}</strong></td>
            </tr>
            """

        # Generate table for HA status
        ha_table = ""
        for ha in ha_status:
            ha_table += f"""
            <tr>
                <td>{ha.get('ha_name', 'N/A')}</td>
                <td><strong>{ha.get('primary_device', 'N/A')} - {ha.get('primary_status', 'N/A')}</strong></td>
                <td>{ha.get('secondary_device', 'N/A')} - {ha.get('secondary_status', 'N/A')}</td>
            </tr>
            """
        # Generate table for ALL network objects
        network_table = ""
        for obj in network_objects:
            network_table += f"""
            <tr>
                <td><strong>{obj.get('name', 'N/A')}</strong></td>
                <td>{obj.get('type', 'N/A')}</td>
                <td>{obj.get('IP', obj.get('value', 'N/A'))}</td>
                <td>{obj.get('id', 'N/A')}</td>
                <td><strong>{obj.get('status', 'N/A')}</strong></td>
            </tr>
            """
        # Generate table for ALL security zones
        security_zone_table = ""
        for zone in security_zones:
            security_zone_table += f"""
            <tr>
                <td><strong>{zone.get('name', 'N/A')}</strong></td>
                <td>{zone.get('type', 'N/A')}</td>
                <td>{zone.get('id', 'N/A')}</td>
                <td><strong>{zone.get('status', 'N/A')}</strong></td>
            </tr>
            """
        # Generate table for ALL interfaces
        interfaces_table = ""
        for intf in interfaces_configured:
            interfaces_table += f"""
            <tr>
            <td><strong>{intf.get('ifname', 'N/A')}</strong></td>
            <td>{intf.get('ip_address', 'N/A')}</td>
            <td>{intf.get('netmask', 'N/A')}</td>
            <td>{intf.get('standby_ip', 'N/A')}</td>
            <td><strong>{intf.get('status', 'N/A')}</strong></td>
            </tr>
            """
        # Generate table for ALL static routes
        routes_table = ""
        for route in static_routes:
            routes_table += f"""
            <tr>
                <td>{route.get('name', 'N/A')}</td>
                <td>{route.get('source', 'N/A')}</td>
                <td>{route.get('next_hop', 'N/A')}</td>
                <td>{route.get('type', 'N/A')}</td>
                <td>{route.get('id', 'N/A')}</td>
                <td><strong>{route.get('status', 'N/A')}</strong></td>
            </tr>
            """
        # Generate table for ALL NAT policies and rules
 
        nat_policy_table = ""
        for policy in nat_policy:
            nat_policy_table += f"""
            <tr>
                <td>{policy.get('name', 'N/A')}</td>
                <td>{policy.get('type', 'N/A')}</td>
                <td>{policy.get('id', 'N/A')}</td>
                <td><strong>{policy.get('status', 'N/A')}</strong></td>
            </tr>
            """
        nat_rules_table = ""
        for rule in nat_rules:
            nat_rules_table += f"""
            <tr>
                <td>{rule.get('name', 'N/A')}</td>
                <td>{rule.get('type', 'N/A')}</td>
                <td>{rule.get('id', 'N/A')}</td>
                <td>{rule.get('source_interface', 'N/A')}</td>
                <td>{rule.get('destination_interface', 'N/A')}</td>
                <td>{rule.get('original_network', 'N/A')}</td>
                <td><strong>{rule.get('status', 'N/A')}</strong></td>
            </tr>
            """
        # Generate table for ALL access policies
        access_policy_table = ""
        for policy in access_policies:
            access_policy_table += f"""
            <tr>
                <td>{policy.get('name', 'N/A')}</td>
                <td>{policy.get('type', 'N/A')}</td>
                <td>{policy.get('id', 'N/A')}</td>
                <td><strong>{policy.get('status', 'N/A')}</strong></td>
            </tr>
            """
        # Generate table for ALL platform settings assignments
        platform_settings_table = ""
        for setting in platform_settings:
            platform_settings_table += f"""
            <tr>
                <td>{setting.get('name', 'N/A')}</td>
                <td>{setting.get('type', 'N/A')}</td>
                <td>{setting.get('id', 'N/A')}</td>
                <td><strong>{setting.get('status', 'N/A')}</strong></td>
            </tr>
            """
        # Get basic deployment info
        ha_name = os.getenv('FW_HOSTNAME_01', 'Unknown') + '_HA'
        fmc_ip = os.getenv('FMC_IP', 'N/A')
        ftd_device_01 = os.getenv('FW_HOSTNAME_01', 'N/A')
        ftd_device_02 = os.getenv('FW_HOSTNAME_02', 'N/A')
        ftd_device_ip_01 = os.getenv('IP_ADD_FW_01', 'N/A')
        ftd_device_ip_02 = os.getenv('IP_ADD_FW_02', 'N/A')

        return f"""
        <html>

        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: #2E8B57;">FTD Configuration Report</h2>
            
            <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
            This is an automated report generated by the automation for the successful deployment of Cisco FTD firewall devices 
            <strong>{ftd_device_01}</strong> and <strong>{ftd_device_02}</strong> in High Availability (HA) configuration.
            </p>
    
            <h3 style="color: #4682B4;">Deployment Summary:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f0f0f0;">
                    <td><strong>Parameter</strong></td>
                    <td><strong>Value</strong></td>
                </tr>
                <tr><td><strong>FTD device 01:</strong></td><td>{ftd_device_01} - {ftd_device_ip_01}</td></tr>
                <tr><td><strong>FTD device 02:</strong></td><td>{ftd_device_02} - {ftd_device_ip_02}</td></tr>
                <tr><td><strong>HA Pair Name:</strong></td><td>{ha_name}</td></tr>
                <tr><td><strong>FMC IP:</strong></td><td>{fmc_ip}</td></tr>
                <tr><td><strong>Deployment Time:</strong></td><td>{deployment_time}</td></tr>
                <tr><td><strong>Total Network Objects:</strong></td><td>{len(network_objects)}</td></tr>
                <tr><td><strong>Total Security Zones:</strong></td><td>{len(security_zones)}</td></tr>
                <tr><td><strong>Total Interfaces Configured:</strong></td><td>{len(interfaces_configured)}</td></tr>
                <tr><td><strong>Total Static Routes:</strong></td><td>{len(static_routes)}</td></tr>
                <tr><td><strong>Total Access Policies:</strong></td><td>{len(access_policies)}</td></tr>
                <tr><td><strong>Total NAT Policies:</strong></td><td>{len(nat_policy)}</td></tr>
                <tr><td><strong>Total NAT Rules:</strong></td><td>{len(nat_rules)}</td></tr>
            </table>
            <h3 style="color: #4682B4;">Device Health Status:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Device Name</th>
                    <th>Health Status</th>
                    <th>Deployment Status</th>
                </tr>
                {health_table}
            </table>
            <h3 style="color: #4682B4;">HA Configuration Status:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>HA Name</th>
                    <th>Primary Device - Status</th>
                    <th>Secondary Device - Status</th>
                </tr>
                {ha_table}
            </table>
            <h3 style="color: #4682B4;">Network Objects:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Object Name</th>
                    <th>Type</th>
                    <th>IP/Network</th>
                    <th>Object ID</th>
                    <th>Status</th>
                </tr>
                {network_table}
            </table>
            
            <h3 style="color: #4682B4;">Security Zones:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Zone Name</th>
                    <th>Type</th>
                    <th>Zone ID</th>
                    <th>Status</th>
                </tr>
                {security_zone_table}
            </table>
            <h3 style="color: #4682B4;">Interfaces:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Interface Name</th>
                    <th>IP Address</th>
                    <th>Subnet Mask</th>
                    <th>Standby IP</th>
                    <th>Status</th>
                </tr>
                {interfaces_table}
            </table>
            <h3 style="color: #4682B4;">Static Routes Created:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Route Name</th>
                    <th>Source</th>
                    <th>Next Hop</th>
                    <th>Type</th>
                    <th>Route ID</th>
                    <th>Status</th>
                </tr>
                {routes_table}
            </table>
            <h3 style="color: #4682B4;">Platform Settings:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Platform Setting Name</th>
                    <th>Type</th>
                    <th>Platform Setting ID</th>
                    <th>Status</th>
                </tr>
                {platform_settings_table}
            </table>
            <h3 style="color: #4682B4;">Access Policies:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Policy Name</th>
                    <th>Type</th>
                    <th>Policy ID</th>
                    <th>Status</th>
                </tr>
                {access_policy_table}
            </table>
            <h3 style="color: #4682B4;">NAT Policies:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Policy Name</th>
                    <th>Type</th>
                    <th>Policy ID</th>
                    <th>Status</th>
                </tr>
                {nat_policy_table}
            </table>

            <h3 style="color: #4682B4;">NAT Rules:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: center;">
                <tr style="background-color: #f0f0f0;">
                    <th>Rule Name</th>
                    <th>Type</th>
                    <th>Rule ID</th>
                    <th>Source Interface</th>
                    <th>Destination Interface</th>
                    <th>Original Network</th>
                    <th>Status</th>
                </tr>
                {nat_rules_table}
            </table>

            <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h3 style="color: #155724; margin-top: 0;">Deployment Status: SUCCESS</h3>
                <p style="margin-bottom: 0;"><strong>FTD configuration completed successfully!</strong></p>
            </div>
        </body>
        </html>
        """
    def send_email_report(self):
        try:
            # Gmail SMTP settings
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = os.getenv('GMAIL_USERNAME')
            sender_password = os.getenv('GMAIL_APP_PASSWORD')
            email_destinations = os.getenv('EMAIL_REPORT_DESTINATION', '').split(',')
            email_destinations = [email.strip() for email in email_destinations if email.strip()]

            if not all([sender_email, sender_password, email_destinations]):
                logger.error("Missing email configuration. Check environment variables.")
                return False
            for email in email_destinations:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = email
                msg['Subject'] = f"FTD Configuration Report - {os.getenv('FW_HOSTNAME_01', 'Unknown')}_HA"

                # Email body with configuration summary
                body = self._generate_report_body()
                msg.attach(MIMEText(body, 'html'))

                # Send email
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                server.quit()

                logger.info(f"Configuration report sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
      
    def execute(self):
        """
        Execute email deployment report generation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.load_devices_templates()

        try:
            logger.info("Starting email report generation...")
            logger.info(f"Found {len(self.email_report_data.get('health_status', []))} health status entries in report")
            logger.info(f"Found {len(self.email_report_data.get('ha_status', []))} HA configurations in report")
            logger.info(f"Found {len(self.email_report_data.get('network_objects', []))} network objects in report")
            logger.info(f"Found {len(self.email_report_data.get('security_zones', []))} security zones in report")
            logger.info(f"Found {len(self.email_report_data.get('interfaces_configured', []))} interfaces in report")
            logger.info(f"Found {len(self.email_report_data.get('static_routes', []))} static routes in report")
            logger.info(f"Found {len(self.email_report_data.get('access_policies', []))} access policies in report")
            logger.info(f"Found {len(self.email_report_data.get('platform_settings', []))} platform settings in report")
            logger.info(f"Found {len(self.email_report_data.get('nat_policy', []))} NAT policies in report")
            logger.info(f"Found {len(self.email_report_data.get('nat_rules', []))} NAT rules in report")
            
            
            if self.send_email_report():
                logger.info("Email report sent successfully")
                return True
            else:
                logger.error("Failed to send email report")
                return False
          
        except Exception as e:
            logger.error(f"Error in email report execution: {e}")
            return False