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
    def _generate_report_body(self):
        """
        Generate the HTML body for the email report.
        """
        network_objects = self.email_report_data.get("network_objects", [])
        security_zones = self.email_report_data.get("security_zones", [])

        # Generate table for ALL network objects
        network_table = ""
        for obj in network_objects:
            network_table += f"""
            <tr>
                <td>{obj.get('name', 'N/A')}</td>
                <td>{obj.get('type', 'N/A')}</td>
                <td>{obj.get('IP', obj.get('value', 'N/A'))}</td>
                <td>{obj.get('id', 'N/A')}</td>
            </tr>
            """
        # Generate table for ALL security zones
        security_zone_table = ""
        for zone in security_zones:
            security_zone_table += f"""
            <tr>
                <td>{zone.get('name', 'N/A')}</td>
                <td>{zone.get('type', 'N/A')}</td>
                <td>{zone.get('id', 'N/A')}</td>
            </tr>
            """
        
        # Get basic deployment info
        ha_name = os.getenv('FW_HOSTNAME_01', 'Unknown') + '_HA'
        fmc_ip = os.getenv('FMC_IP', 'N/A')
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: #2E8B57;">FTD Configuration Report</h2>
            
            <h3 style="color: #4682B4;">Deployment Summary:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f0f0f0;">
                    <td><strong>Parameter</strong></td>
                    <td><strong>Value</strong></td>
                </tr>
                <tr><td><strong>HA Pair Name:</strong></td><td>{ha_name}</td></tr>
                <tr><td><strong>FMC IP:</strong></td><td>{fmc_ip}</td></tr>
                <tr><td><strong>Total Network Objects:</strong></td><td>{len(network_objects)}</td></tr>
                <tr><td><strong>Total Security Zones:</strong></td><td>{len(security_zones)}</td></tr>
            </table>
            
            <h3 style="color: #4682B4;">Network Objects Created:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f0f0f0;">
                    <th>Object Name</th>
                    <th>Type</th>
                    <th>IP/Network</th>
                    <th>Object ID</th>
                </tr>
                {network_table}
            </table>
            
            <h3 style="color: #4682B4;">Security Zones Created:</h3>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f0f0f0;">
                    <th>Zone Name</th>
                    <th>Type</th>
                    <th>Zone ID</th>
                </tr>
                {security_zone_table}
            </table>

            <h3 style="color: #4682B4;">Configuration Steps:</h3>
            <ul>
                <li>Network Objects Created ({len(network_objects)} total)</li>
                <li>Security Zones Created ({len(security_zones)} total)</li>
                <li>NAT Policy Applied</li>
            </ul>
            
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
            recipient_email = os.getenv('EMAIL_REPORT_DESTINATION')

            if not all([sender_email, sender_password, recipient_email]):
                logger.error("Missing email configuration. Check environment variables.")
                return False

            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
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
            
            logger.info(f"Configuration report sent to {recipient_email}")
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
            logger.info(f"Found {len(self.email_report_data.get('network_objects', []))} network objects in report")
            logger.info(f"Found {len(self.email_report_data.get('security_zones', []))} security zones in report")
            
            
            if self.send_email_report():
                logger.info("Email report sent successfully")
                return True
            else:
                logger.error("Failed to send email report")
                return False
          
        except Exception as e:
            logger.error(f"Error in email report execution: {e}")
            return False

    def load_devices_templates(self):
        try:
            from utils_ftd import EMAIL_REPORT_DATA_FILE
            
            with open(EMAIL_REPORT_DATA_FILE, 'r') as f0:
                self.email_report_data = json.load(f0)
                logger.info("Loaded email report data dictionary")
        except FileNotFoundError:
            logger.warning("Email report data file not found, using empty data")
            self.email_report_data = {"network_objects": [], "security_zones": []}
        except Exception as e:
            logger.error(f"Error loading email report data: {e}")
            self.email_report_data = {"network_objects": [], "security_zones": []}