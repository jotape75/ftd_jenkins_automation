"""
Main orchestrator for PA Firewall Jenkins Automation

Command-line entry point for Jenkins-based Palo Alto firewall deployment.
Executes individual automation steps based on arguments, with comprehensive
logging and error handling for CI/CD pipeline integration.

Key Features:
- Step-by-step execution via command line arguments (--step)
- Centralized logging with date-based log files and console output
- Dynamic step importing and execution with success/failure reporting
- Jenkins-compatible exit codes for pipeline flow control
- Project root detection for flexible deployment environments
- Comprehensive error handling with detailed logging for troubleshooting
"""

import argparse
import sys
import logging
import datetime
import os
from pathlib import Path

# Get project root and define log file path
def get_project_root():
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

PROJECT_ROOT = get_project_root()
LOG_DIR = PROJECT_ROOT / "log"

# Create log directory if it doesn't exist
LOG_DIR.mkdir(exist_ok=True)  # This creates the directory!

# Create log file with date
date_str = datetime.datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / f"jenkins_ftd_automation_{date_str}.log"

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',  # Append mode instead of overwrite
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Log to console for Jenkins
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger()

def main():
    """
    Main function to handle Jenkins step execution.
    """
    parser = argparse.ArgumentParser(description='FTD Firewall Jenkins Automation') 
    parser.add_argument('--step', required=True, help='Step to execute')
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting FTD Automation - Log file: {LOG_FILE}")
        logger.info(f"Executing step: {args.step}")
        
    
        if args.step == 'api_keys':
            from steps.step_01_api_keys import Step01_APIKeys
            step = Step01_APIKeys()
            success = step.execute()
        elif args.step == 'add_dev_fmc':
            from steps.step_02_add_dev_fmc import Step02_ADD_DEV_FMC
            step = Step02_ADD_DEV_FMC()
            success = step.execute()
        elif args.step == 'conf_ha':
            from steps.step_03_conf_ha import Step03_HAConfig
            step = Step03_HAConfig()
            success = step.execute()
        elif args.step == 'ftd_conf':
            from steps.step_04_ftd_conf import Step04_FTD_CONF
            step = Step04_FTD_CONF()
            success = step.execute()  
        elif args.step == 'fmc_deployment':
            from steps.step_05_fmc_deployment import Step05_FMC_DEPLOYMENT
            step = Step05_FMC_DEPLOYMENT()
            success = step.execute()
        else:
            logger.error(f"Unknown step: {args.step}")
            available_steps = ['api_keys', 'ha_interfaces', 'ha_config']
            logger.info(f"Available steps: {', '.join(available_steps)}")
            sys.exit(1)
        
        if success:
            logger.info(f"Step {args.step} completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Step {args.step} failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error executing step {args.step}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()