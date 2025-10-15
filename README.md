# 🔥🧱 Jenkins Cisco FTD Firewall HA Automation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Network Automation](https://img.shields.io/badge/Network-Automation-green.svg)](https://github.com/username/jenkins_ftd_automation)
[![Cisco FTD](https://img.shields.io/badge/Cisco-FTD-blue.svg)](https://www.cisco.com/c/en/us/products/security/firewalls/)
[![Jenkins](https://img.shields.io/badge/Jenkins-Pipeline-blue.svg)](https://jenkins.io/)

A comprehensive Jenkins-based automation solution for deploying Cisco FTD (Firepower Threat Defense) firewall High Availability (HA) pairs with complete network configuration through Firepower Management Center (FMC). This automation provides a form-based interface for dynamic configuration deployment without manual file editing.

## 📋 Overview

This automation eliminates manual FTD configuration by providing a **form-based Jenkins interface** for dynamic deployment. The solution operates entirely through Jenkins and FMC REST API, making firewall deployments consistent, auditable, and easily repeatable across environments.

## ⚡ Key Features

- **🎯 Centralized Execution**: Complete automation through Jenkins with FMC REST API integration
- **📋 Form-Based Interface**: All parameters configurable through Jenkins web interface
- **🔧 Dynamic Configuration**: JSON templates updated automatically using Jenkins parameters
- **📊 Pipeline Visibility**: Real-time progress tracking and comprehensive logging
- **🔒 Secure Credential Handling**: Password management with automatic cleanup
- **📁 Audit Trail**: Automatic artifact archival and email reporting
- **🔄 HA-Aware Deployment**: Intelligent device discovery and configuration targeting
- **📧 Email Reporting**: Comprehensive HTML reports with deployment status

## 📂 Repository Setup

### 🐙 GitHub Repository
```bash
# Clone the repository
git clone https://github.com/username/jenkins_ftd_automation.git

# Navigate to project directory
cd jenkins_ftd_automation

# Install dependencies
pip install -r requirements.txt
```

## 🏗️ Architecture

### 🚀 Pipeline Stages

1. **API Key Generation** - Authenticate with FMC REST API
2. **Device Registration** - Add FTD devices to FMC management
3. **HA Configuration** - Configure High Availability pairing
4. **Network Configuration** - Objects, zones, interfaces, routing, policies, NAT
5. **Configuration Deployment** - Deploy configurations to FTD devices
6. **Email Reporting** - Generate and send deployment status reports

### 📁 File Structure

```
jenkins_ftd_automation/
├── src/
│   ├── main.py                     # Pipeline orchestrator
│   ├── update_templates.py         # Template preprocessing
│   └── steps/
│       ├── step_01_api_keys.py     # FMC API authentication
│       ├── step_02_add_dev_fmc.py  # Device registration
│       ├── step_03_conf_ha.py      # HA configuration
│       ├── step_04_ftd_conf.py     # Network configuration
│       ├── step_05_fmc_deployment.py # Configuration deployment
│       └── step_06_email_report.py # Email reporting
├── data/payload/                   # JSON configuration templates
│   ├── device_registration.json    # Device registration template
│   ├── ha_config.json             # HA configuration template
│   ├── host_objects.json          # Network host objects
│   ├── network_objects.json       # Network subnet objects
│   ├── security_zones.json        # Security zone definitions
│   ├── interface_config.json      # Physical interface configuration
│   ├── default_route.json         # Static routing configuration
│   ├── nat_policy.json            # NAT policy template
│   └── nat_rules.json             # NAT rule configurations
├── log/                           # Execution logs
├── Jenkinsfile                    # Pipeline definition
├── README.md                      # Project documentation
└── requirements.txt               # Python dependencies
```

### 🔧 Jenkins Integration
1. **Create New Pipeline Job** in Jenkins
2. **Pipeline from SCM** → Select Git
3. **Repository URL**: `https://github.com/username/jenkins_ftd_automation.git`
4. **Script Path**: `Jenkinsfile`
5. **Configure Gmail credentials** for email reporting
6. **Save and Build with Parameters**

## ⚙️ Configuration Parameters

### 🔗 FMC Connection
- **FMC IP Address** - Firepower Management Center IP (e.g., `192.168.0.201`)
- **FMC Username** - Administrative user for FMC API access (e.g., `api_user`)
- **FMC Password** - Secure password for authentication

### 🔥 FTD Device Configuration
- **FTD Device 01** - Primary FTD hostname (e.g., `ciscoftd03`)
- **FTD Device 02** - Secondary FTD hostname (e.g., `ciscoftd04`)
- **FTD Device 01 IP** - Primary device management IP (e.g., `192.168.0.203`)
- **FTD Device 02 IP** - Secondary device management IP (e.g., `192.168.0.204`)
- **FTD REGKEY** - Registration key for FMC device pairing

### 🌐 Network Configuration
- **Inside Interface IP** - Internal network interface IP (e.g., `10.10.10.5/24`)
- **Outside Interface IP** - External network interface IP (e.g., `200.200.200.2/24`)
- **DMZ Interface IP** - DMZ network interface IP (e.g., `10.30.30.5/24`)
- **HA Standby IPs** - Failover IP addresses for each interface

### 🛡️ Routing & Gateway
- **Default Gateway** - Network gateway IP (e.g., `200.200.200.1`)
- **Inside Network** - Internal network subnet (e.g., `10.10.10.0/24`)
- **DMZ Network** - DMZ network subnet (e.g., `10.30.30.0/24`)

### 🔒 NAT Configuration
- **Source NAT IP** - IP address for outbound NAT (e.g., `200.200.200.10`)

### ⚙️ Platform Settings
- **Global Platform Settings Assignment** - Choose platform settings for FTD devices

### 📧 Email Reporting
- **Email Recipients** - Comma-separated email addresses for deployment reports

## 🚀 Usage

### 📋 Prerequisites

1. **Jenkins Environment** with Python 3.x support
2. **FMC Access** with REST API enabled
3. **Network Access** to FTD device management interfaces
4. **API User** configured on FMC with appropriate permissions
5. **Gmail Credentials** configured in Jenkins for email reporting

### 🔧 Deployment Process

1. **Access Jenkins Pipeline**
   ```
   Navigate to: Jenkins → Your Pipeline Job → Build with Parameters
   ```

2. **Configure Parameters**
   - Fill out the form-based interface with network details
   - Specify FMC and FTD device information
   - Provide API credentials and email recipients

3. **Execute Pipeline**
   ```
   Review settings → Click "Build"
   ```

4. **Monitor Progress**
   - Real-time stage execution in Jenkins console
   - Detailed logging for each configuration step
   - Email report sent upon completion


## ⭐ Key Features

### 🚀 **Complete FTD HA Deployment**
Comprehensive automation covering device registration, HA configuration, network setup, and policy deployment.

### 🔄 **Template-Driven Configuration**
JSON templates are dynamically updated with Jenkins parameters, ensuring consistency and reducing human error.

### 🛡️ **FMC Integration**
Native REST API integration with Firepower Management Center for centralized management and deployment.

### 📊 **Comprehensive Monitoring**
- Real-time deployment status tracking
- Device health monitoring
- HA synchronization verification
- Detailed success/failure reporting

### 📧 **Professional Email Reporting**
- HTML email reports with deployment summary
- Color-coded health status indicators
- Complete configuration inventory
- Multiple recipient support

### 🔧 **Conflict Detection**
- Existing object detection and resolution
- Policy assignment management (PUT/POST logic)
- Graceful handling of configuration conflicts

## 📊 Network Components Configured

| Component | Configuration Details |
|-----------|----------------------|
| **Network Objects** | Host and subnet objects for gateway and networks |
| **Security Zones** | Inside, Outside, DMZ zones with interface assignments |
| **Physical Interfaces** | IP configuration with HA standby addresses |
| **Static Routes** | Default route with gateway object references |
| **NAT Policies** | Auto-NAT rules for outbound traffic |
| **Platform Settings** | Device-specific platform configurations |
| **HA Configuration** | Failover interfaces and active/standby pairing |

## 📝 Email Reporting

The automation generates comprehensive HTML email reports including:

- **Deployment Summary**: Device information, deployment time, component counts
- **Device Health Status**: Color-coded health indicators (🟢🟡🔴🔵)
- **HA Configuration**: Primary/secondary device status and roles
- **Network Objects**: All created objects with status
- **Security Zones**: Zone assignments and interface mappings
- **Interface Configuration**: IP addresses and HA standby configurations
- **Routing**: Static route configurations
- **Policy Assignments**: Platform settings and policy deployments

## 📝 Logging and Troubleshooting

### 📋 Log Files
- **Execution Logs**: `log/jenkins_ftd_automation_YYYY-MM-DD.log`
- **Jenkins Console**: Real-time pipeline output
- **Email Reports**: Comprehensive deployment status

### ⚠️ Common Issues
- **API Authentication**: Verify FMC credentials and REST API access
- **Device Registration**: Ensure network connectivity to FTD devices
- **HA Establishment**: Allow sufficient time for HA synchronization
- **Template Errors**: Check parameter formatting and JSON structure

## 🔒 Security Considerations

- **Credential Management**: Passwords handled securely with automatic cleanup
- **API Access**: Uses dedicated API users with minimal required permissions
- **Network Security**: Ensure FMC and FTD management interfaces are secured
- **Email Security**: Gmail app passwords for secure SMTP authentication

## 🤝 Contributing

Contributions focused on:
- Enhanced error handling and recovery mechanisms
- Additional configuration templates and features
- Extended monitoring and reporting capabilities
- Integration with network management systems

## 📞 Contact

**JP**

For questions or support:

[![GitHub](https://img.shields.io/badge/GitHub-jotape75-blue?style=flat&logo=github)](https://github.com/jotape75)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-jotape75-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/jotape75)
[![Email](https://img.shields.io/badge/Email-jotape75%40domain.com-red?style=flat&logo=gmail)](mailto:jotape75@domain.com)

## 📄 License

MIT License - Enterprise deployment automation for Cisco FTD infrastructure.

---

🚀 **Automated Cisco FTD deployment made simple with Jenkins!**