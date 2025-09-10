"""
Utility functions and constants for PA Firewall automation

Provides shared utilities, file paths, and common functions for Jenkins-based
Palo Alto firewall automation. Handles project structure navigation and
commit operations across multiple automation steps.

Key Features:
- Dynamic project root detection for Jenkins and local environments
- Centralized template file path management
- Shared commit monitoring utility with job tracking and timeout handling
- Path resolution using pathlib for cross-platform compatibility
- SSL and timeout configuration for API operations
"""
import os
import json
from pathlib import Path

def get_project_root():
    """
    Get the project root directory (where Jenkinsfile is located).
    Works in both local development and Jenkins containers.
    """
    current_file = Path(__file__).resolve()
    # Navigate up from src/utils_pa.py to project root
    project_root = current_file.parent.parent
    return project_root

# Project paths (hardcoded constants - more reliable)
PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data" # navigate to data directory
PAYLOAD_DIR = DATA_DIR / "payload" # navigate to payload directory

# File paths CONSTANTS

# File paths CONSTANTS

FTD_DEVICES_TEMPLATE = f"{get_project_root()}/data/payload/fmc_devices.json"
PA_HA_INTERFACE_TEMPLATE = f"{get_project_root()}/data/payload/paloalto_interface_ha_template.xml"
PA_HA_CONFIG_TEMPLATE = f"{get_project_root()}/data/payload/paloalto_ha_template_config.xml"
PA_ZONES_TEMPLATE = f"{get_project_root()}/data/payload/zones.xml"
PA_ROUTER_TEMPLATE = f"{get_project_root()}/data/payload/virtual_router_template.xml"
PA_ROUTES_TEMPLATE = f"{get_project_root()}/data/payload/static_route_template.xml"
PA_SECURITY_TEMPLATE = f"{get_project_root()}/data/payload/security_policy_template.xml"
PA_NAT_TEMPLATE = f"{get_project_root()}/data/payload/source_nat_template.xml"
# Remove PA_VIRTUAL_ROUTER_TEMPLATE (duplicate of PA_ROUTER_TEMPLATE)

def file_path():
    """
    Return file paths for templates.
    No external JSON dependency - more reliable for Jenkins.
    Credentials are now handled by Jenkins parameters, not files.
    """
    return (
        str(PA_HA_CONFIG_TEMPLATE),
        str(PA_HA_INTERFACE_TEMPLATE),  
        str(PA_INTERFACE_TEMPLATE),
        str(PA_ZONES_TEMPLATE),
        str(PA_ROUTER_TEMPLATE),
        str(PA_ROUTES_TEMPLATE),
        str(PA_SECURITY_TEMPLATE),
        str(PA_NAT_TEMPLATE)
    )
def commit_changes(pa_credentials, api_keys_list, step_name=""):
    """
    Commit configuration changes and monitor until completion.
    Shared utility for all automation steps.
    
    Args:
        pa_credentials: List of device credentials
        api_keys_list: List of API headers with keys
        step_name: Name of the step for logging purposes
        
    Returns:
        bool: True if all commits successful, False otherwise
    """
    import requests
    import xml.etree.ElementTree as ET
    import time
    import logging
    
    # Disable SSL warnings
    requests.packages.urllib3.disable_warnings()
    logger = logging.getLogger()
    
    try:
        jobid_dict = {}
        ready_devices = {}
        
        logger.info(f"Starting commit operations for {step_name}...")
        
        # Step 1: Start commits and collect job IDs
        for device, headers in zip(pa_credentials, api_keys_list):  
            try:
                commit_url = f"https://{device['host']}/api/"
                commit_params = {
                    'type': 'commit',
                    'cmd': '<commit></commit>',
                    'key': headers['X-PAN-KEY']  
                }
                
                response = requests.get(commit_url, params=commit_params, verify=False, timeout=60)
                
                if response.status_code == 200:
                    xml_response = response.text
                    root = ET.fromstring(xml_response)
                    result = root.find(".//result")
                    if result is not None:
                        jobid = result.findtext("job")
                        unique_key = f"{device['host']}_{jobid}"
                        jobid_dict[unique_key] = {
                            'device': device,
                            'headers': headers,
                            'host': device['host'],
                            'jobid': jobid
                        }
                        logger.info(f"Commit job ID for {device['host']}: {jobid}")
                else:
                    logger.error(f"Failed to start commit on {device['host']}: {response.status_code}")
                    return False
            except Exception as e:
                logger.error(f"Error committing changes for {device['host']}: {e}")
                return False
        
        if not jobid_dict:
            logger.error("No commit jobs started")
            return False
        
        # Step 2: Monitor jobs until completion
        logger.info(f"Monitoring {len(jobid_dict)} commit jobs...")
        max_wait_time = 600  # 10 minutes max wait
        start_time = time.time()
        
        while jobid_dict and (time.time() - start_time) < max_wait_time:
            completed_jobs = []
            for unique_key, job_info in jobid_dict.items():
                host = job_info['host']
                jobid = job_info['jobid']
                headers = job_info['headers']
                
                job_url = f"https://{host}/api/"
                job_params = {
                    'type': 'op',
                    'cmd': f'<show><jobs><id>{jobid}</id></jobs></show>',
                    'key': headers['X-PAN-KEY']
                }
                job_response = requests.get(job_url, params=job_params, verify=False, timeout=30)
                
                if job_response.status_code == 200:
                    job_xml_response = job_response.text
                    root = ET.fromstring(job_xml_response)
                    job = root.find(".//job")
                    
                    if job is not None:
                        job_status = job.findtext("status")
                        job_progress = job.findtext("progress", "0")
                        job_result = job.findtext("result", "")
                        
                        if job_status == "ACT":
                            logger.info(f"Commit running for {host}, progress {job_progress}%")
                        elif job_status == "FIN":
                            if job_result == "OK":
                                logger.info(f"Commit completed successfully for {host}")
                                ready_devices[host] = True
                                completed_jobs.append(unique_key)
                            else:
                                logger.error(f"Commit failed on {host}: {job_result}")
                                return False
            
            # Remove completed jobs
            for unique_key in completed_jobs:
                if unique_key in jobid_dict:
                    del jobid_dict[unique_key]
            
            if not jobid_dict:
                break
            time.sleep(15)
        
        if jobid_dict:
            logger.error(f"Timeout waiting for commits to complete for {step_name}")
            return False
        
        logger.info(f"All commits completed successfully for {step_name}!")
        return True
        
    except Exception as e:
        logger.error(f"Error in commit process for {step_name}: {e}")
        return False