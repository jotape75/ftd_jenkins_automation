/*
 * Jenkins Pipeline for Cisco FTD Firewall HA Deployment
 * 
 * Automated deployment pipeline for configuring High Availability Cisco FTD
 * firewall pairs with comprehensive network configuration. Provides a form-based
 * interface for dynamic parameter input and executes step-by-step automation.
 * 
 * Pipeline Stages:
 * 1. Repository setup and dependency installation
 * 2. Template preprocessing with Jenkins parameters
 * 3. FTD initial configuration (SSH manager setup)
 * 4. FMC API key generation for firewall authentication
 * 5. Device registration with FMC
 * 6. HA configuration and enablement
 * 7. Complete firewall configuration (interfaces, zones, routing, policies, NAT)
 * 8. Configuration commit and HA synchronization
 * 
 * Key Features:
 * - Form-based parameter input for dynamic configuration
 * - Support for multiple FTD devices in HA configuration
 * - Combined interface selection (Interface | Name | Security Zone)
 * - Comprehensive error handling and logging
 * - Artifact archival for audit and troubleshooting
 * - Password security with automatic cleanup
 */

pipeline {
    agent any
    environment {
        GMAIL_USERNAME = credentials('gmail-username')
        GMAIL_APP_PASSWORD = credentials('gmail-app-password')
    }
    parameters {
        string(name: 'EMAIL_REPORT_DESTINATION', defaultValue: '', description: 'Add email addresses to receive the report (comma-separated for multiple recipients)')
        // FMC parameters
        string(name: 'FMC_IP', defaultValue: '192.168.0.201', description: 'FMC IP Address')
        string(name: 'FMC_USERNAME', defaultValue: 'api_user', description: 'FMC Username')
        password(name: 'FMC_PASSWORD', description: 'FMC Password')

        // FTD parameters
        string(name: 'FW_HOSTNAME_01', defaultValue: 'ciscoftd01', description: 'Cisco FTD 01 Hostname')
        string(name: 'IP_ADD_FW_01', defaultValue: '192.168.0.202', description: 'Cisco FTD 01 IP Address')
        string(name: 'FW_HOSTNAME_02', defaultValue: 'ciscoftd02', description: 'Cisco FTD 02 Hostname')
        string(name: 'IP_ADD_FW_02', defaultValue: '192.168.0.203', description: 'Cisco FTD 02 IP Address')
        password(name: 'REGKEY', description: 'Key for FMC Registration')

        // HA and Network parameters
        choice(name: 'HA_INTERFACE', choices: ['GigabitEthernet0/3', 'GigabitEthernet0/4', 'GigabitEthernet0/5'], description: 'HA Interface')

        // Combined interface configurations
        choice(name: 'INSIDE_INTERFACE', choices: ['GigabitEthernet0/0','GigabitEthernet0/1','GigabitEthernet0/2','GigabitEthernet0/3','GigabitEthernet0/4'], description: 'Inside: Interface | Name')
        string(name: 'INSIDE_INTERFACE_NAME', defaultValue: 'Inside', description: 'Inside Interface Name')
        string(name: 'INSIDE_SEC_ZONE', defaultValue: 'Inside_Sec_Zone', description: 'Inside Security Zone')
        string(name: 'INSIDE_IP', defaultValue: '192.168.1.1', description: 'Inside Interface IP Address')
        string(name: 'INSIDE_MASK', defaultValue: '255.255.255.0', description: 'Inside Interface Subnet Mask')
        string(name: 'INSIDE_STANDBY_IP', defaultValue: '192.168.1.2', description: 'Inside Interface Standby IP')
        string(name:'INSIDE_NETWORK', defaultValue: '192.168.1.0/24', description: 'Inside Networks')

        // Outside interface configurations

        choice(name: 'OUTSIDE_INTERFACE', choices: ['GigabitEthernet0/0','GigabitEthernet0/1','GigabitEthernet0/2'], description: 'Outside: Interface | Name')
        string(name: 'OUTSIDE_INTERFACE_NAME', defaultValue: 'Outside', description: 'Outside Interface Name')
        string(name: 'OUTSIDE_SEC_ZONE', defaultValue: 'Outside_Sec_Zone', description: 'Outside Security Zone')
        string(name: 'OUTSIDE_IP', defaultValue: '10.0.0.1', description: 'Outside Interface IP Address')
        string(name: 'OUTSIDE_MASK', defaultValue: '255.255.255.0', description: 'Outside Interface Subnet Mask')
        string(name: 'OUTSIDE_STANDBY_IP', defaultValue: '10.0.0.2', description: 'Outside Interface Standby IP')
        string(name:'OUTSIDE_NETWORK', defaultValue: '10.0.0.0/24', description: 'Outside Networks')


        // DMZ interface configurations

        choice(name: 'DMZ_INTERFACE', choices: ['GigabitEthernet0/0','GigabitEthernet0/1','GigabitEthernet0/2'], description: 'DMZ: Interface | Name')
        string(name: 'DMZ_INTERFACE_NAME', defaultValue: 'DMZ', description: 'DMZ Interface Name')
        string(name: 'DMZ_SEC_ZONE', defaultValue: 'DMZ_Sec_Zone', description: 'DMZ Security Zone') 
        string(name: 'DMZ_IP', defaultValue: '172.16.1.1', description: 'DMZ Interface IP Address')
        string(name: 'DMZ_STANDBY_IP', defaultValue: '172.16.1.2', description: 'DMZ Interface Standby IP')
        string(name: 'DMZ_MASK', defaultValue: '255.255.255.0', description: 'DMZ Interface Subnet Mask')
        string(name:'DMZ_NETWORK', defaultValue: '172.16.1.0/24', description: 'DMZ Networks')

        // Default route
        string(name: 'DEFAULT_ROUTE_GATEWAY', defaultValue: '10.10.10.1', description: 'Default Route Gateway')
        
        //Platform settings assignment
        string(name: 'PLATFORM_SETTINGS_NAME', defaultValue: 'Global Platform Settings', description: 'Platform Settings Name in FMC')
    }
    
    stages {
        stage('Pull Repository & Setup') {
            steps {
                cleanWs()
                git branch: 'main', url: 'https://github.com/jotape75/ftd_jenkins_automation.git'
                sh '''
                    echo "Setting up environment..."
                    python3 --version
                    pip3 --version
                    pip3 install -r requirements.txt
                '''
            }
        }
        
        stage('Update Configuration Templates') {
            steps {
                script {
                    echo "Setting environment variables and updating templates..."
                    
                    // FMC and FTD parameters
                    env.EMAIL_REPORT_DESTINATION = params.EMAIL_REPORT_DESTINATION
                    env.FMC_IP = params.FMC_IP
                    env.FMC_USERNAME = params.FMC_USERNAME
                    env.FMC_PASSWORD = params.FMC_PASSWORD
                    env.FW_HOSTNAME_01 = params.FW_HOSTNAME_01
                    env.FW_HOSTNAME_02 = params.FW_HOSTNAME_02
                    env.IP_ADD_FW_01 = params.IP_ADD_FW_01
                    env.IP_ADD_FW_02 = params.IP_ADD_FW_02
                    env.REGKEY = params.REGKEY
                    env.HA_INTERFACE = params.HA_INTERFACE
                    
                    // Parse combined interface parameters

                    
                    // Set parsed interface values
                    env.INSIDE_INTERFACE = params.INSIDE_INTERFACE
                    env.INSIDE_INTERFACE_NAME = params.INSIDE_INTERFACE_NAME
                    env.INSIDE_SEC_ZONE = params.INSIDE_SEC_ZONE
                    env.INSIDE_IP = params.INSIDE_IP
                    env.INSIDE_MASK = params.INSIDE_MASK
                    env.INSIDE_STANDBY_IP = params.INSIDE_STANDBY_IP
                    env.INSIDE_NETWORK = params.INSIDE_NETWORK

                    env.OUTSIDE_INTERFACE = params.OUTSIDE_INTERFACE
                    env.OUTSIDE_INTERFACE_NAME = params.OUTSIDE_INTERFACE_NAME
                    env.OUTSIDE_SEC_ZONE = params.OUTSIDE_SEC_ZONE
                    env.OUTSIDE_IP = params.OUTSIDE_IP
                    env.OUTSIDE_MASK = params.OUTSIDE_MASK
                    env.OUTSIDE_STANDBY_IP = params.OUTSIDE_STANDBY_IP
                    env.OUTSIDE_NETWORK = params.OUTSIDE_NETWORK
                    

                    env.DMZ_INTERFACE = params.DMZ_INTERFACE
                    env.DMZ_INTERFACE_NAME = params.DMZ_INTERFACE_NAME
                    env.DMZ_SEC_ZONE = params.DMZ_SEC_ZONE
                    env.DMZ_IP = params.DMZ_IP
                    env.DMZ_MASK = params.DMZ_MASK
                    env.DMZ_STANDBY_IP = params.DMZ_STANDBY_IP
                    env.DMZ_NETWORK = params.DMZ_NETWORK
                    

                    // Default route
                    env.DEFAULT_ROUTE_GATEWAY = params.DEFAULT_ROUTE_GATEWAY
                    env.PLATFORM_SETTINGS_NAME = params.PLATFORM_SETTINGS_NAME

                    sh 'python3 src/update_templates.py'
                    
                    echo "Configuration Summary:"
                    echo "Target FMC: ${params.FMC_IP}"
                    echo "FTD Devices: ${params.FW_HOSTNAME_01}(${params.IP_ADD_FW_01}), ${params.FW_HOSTNAME_02}(${params.IP_ADD_FW_02})"
                    echo "HA Interface: ${params.HA_INTERFACE}"
                    echo "INSIDE: ${params.INSIDE_INTERFACE}(${params.INSIDE_INTERFACE_NAME}) - ${params.INSIDE_IP}/${params.INSIDE_MASK} [${params.INSIDE_SEC_ZONE}]"
                    echo "OUTSIDE: ${params.OUTSIDE_INTERFACE}(${params.OUTSIDE_INTERFACE_NAME}) - ${params.OUTSIDE_IP}/${params.OUTSIDE_MASK} [${params.OUTSIDE_SEC_ZONE}]"
                    echo "DMZ: ${params.DMZ_INTERFACE}(${params.DMZ_INTERFACE_NAME}) - ${params.DMZ_IP}/${params.DMZ_MASK} [${params.DMZ_SEC_ZONE}]"
                }
            }
        }
        stage('Generate FMC API Key') {
            steps {
                sh 'python3 src/main.py --step api_keys'
            }
        }
        
        stage('Add devices to FMC') {
            steps {
                sh 'python3 src/main.py --step add_dev_fmc'
            }
        }
        
        stage('Configure HA Settings') {
            steps {
                sh 'python3 src/main.py --step conf_ha'
            }
        }
        stage('Configure FTD') {
            steps {
                sh 'python3 src/main.py --step ftd_conf'
            }
        }
        stage('FMC FINAL DEPLOYMENT') {
            steps {
                sh 'python3 src/main.py --step fmc_deployment'
            }
        }
        stage('SEND DEPLOYMENT EMAIL REPORT') {
            steps {
                sh 'python3 src/main.py --step email_report'
            }
        }

    }
    
    post {
        always {
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
            script {
                // Clean up sensitive environment variables
                env.FMC_PASSWORD = ""
                env.REGKEY = ""
                env.SSH_ADMIN_PASSWORD = ""
            }
        }
        success {
            echo "FTD Automation completed successfully!"
            echo "Devices ${params.FW_HOSTNAME_01}, ${params.FW_HOSTNAME_02} processed successfully"
            echo "FMC IP: ${params.FMC_IP}"
            echo "HA configured on interface: ${params.HA_INTERFACE}"
        }
        failure {
            echo "FTD Automation failed. Check logs for details."
            echo "Review the archived log files for troubleshooting information."
        }
    }
}