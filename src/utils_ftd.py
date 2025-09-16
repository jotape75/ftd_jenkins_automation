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
    # Navigate up from src/utils_ftd.py to project root
    project_root = current_file.parent.parent
    return project_root

# Project paths (hardcoded constants - more reliable)
PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data" # navigate to data directory
PAYLOAD_DIR = DATA_DIR / "payload" # navigate to payload directory

# File paths CONSTANTS

FTD_DEVICES_TEMPLATE = f"{get_project_root()}/data/payload/fmc_devices.json"
FTD_HA_TEMPLATE = f"{get_project_root()}/data/payload/fmc_ha_payload.json"
