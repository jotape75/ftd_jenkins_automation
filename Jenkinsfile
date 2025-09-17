/*
 * Jenkins Pipeline for Palo Alto Firewall HA Deployment
 * 
 * Automated deployment pipeline for configuring High Availability Palo Alto
 * firewall pairs with comprehensive network configuration. Provides a form-based
 * interface for dynamic parameter input and executes step-by-step automation.
 * 
 * Pipeline Stages:
 * 1. Repository setup and dependency installation
 * 2. Template preprocessing with Jenkins parameters
 * 3. API key generation for firewall authentication
 * 4. HA interface configuration and enablement
 * 5. HA group settings and IP assignment
 * 6. Active firewall identification
 * 7. Complete firewall configuration (interfaces, zones, routing, policies, NAT)
 * 8. Configuration commit and HA synchronization
 * 
 * Key Features:
 * - Form-based parameter input for dynamic configuration
 * - Support for multiple firewall devices in HA configuration
 * - Comprehensive error handling and logging
 * - Artifact archival for audit and troubleshooting
 * - Password security with automatic cleanup
 */

pipeline {
    agent any
    
    parameters {
        string(name: 'FMC_IP', defaultValue: '192.168.0.201', description: 'FMC IP Addresses')
        string(name: 'USERNAME', defaultValue: 'api_user', description: 'FMC Username')
        password(name: 'PASSWORD', description: 'FMC Password')
        string(name: 'FW_HOSTNAME_01', defaultValue: 'ciscoftd01', description: 'Cisco FTD 01 Hostname')
        string(name: 'IP_ADD_FW_01', defaultValue: '192.168.0.202', description: 'Cisco FTD 01 IP Address')
        string(name: 'FW_HOSTNAME_02', defaultValue: 'ciscoftd02', description: 'Cisco FTD 02 Hostname')
        string(name: 'IP_ADD_FW_02', defaultValue: '192.168.0.203', description: 'Cisco FTD 02 IP Address')
        password(name: 'REGKEY', description: 'Key for FMC devices registration')
        choice(name: 'HA_INTERFACE', choices: ['GigabitEthernet0/3', 'GigabitEthernet0/4', 'GigabitEthernet0/5'], description: 'HA Interface')
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
                    
                    // Set environment variables with CORRECT parameter names
                    env.FMC_IP = params.FMC_IP
                    env.USERNAME = params.USERNAME
                    env.PASSWORD = params.PASSWORD
                    env.FW_HOSTNAME_01 = params.FW_HOSTNAME_01
                    env.FW_HOSTNAME_02 = params.FW_HOSTNAME_02
                    env.IP_ADD_FW_01 = params.IP_ADD_FW_01
                    env.IP_ADD_FW_02 = params.IP_ADD_FW_02
                    env.REGKEY = params.REGKEY
                    env.HA_INTERFACE = params.HA_INTERFACE

                    sh 'python3 src/update_templates.py'
                    
                    echo "Configuration Summary:"
                    echo "Target FMC: ${params.FMC_IP}"
                    echo "FTD Devices  IP: ${params.FW_HOSTNAME_01}, ${params.IP_ADD_FW_01}"
                    echo "FTD Devices  IP: ${params.FW_HOSTNAME_02}, ${params.IP_ADD_FW_02}"
                    echo "HA Interface: ${params.HA_INTERFACE}"
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
    }
    // stages {
    //     stage('Configure HA Settings') {
    //         steps {
    //             sh 'python3 src/main.py --step ha_config'
    //         }
    //     }
        
    //     stage('Identify Active Firewall') {
    //         steps {
    //             sh 'python3 src/main.py --step identify_active'
    //         }
    //     }
        
    //     stage('Complete Firewall Configuration') {
    //         steps {
    //             sh 'python3 src/main.py --step firewall_config'
    //         }
    //     }
        
    //     stage('Commit & Sync Configuration') {
    //         steps {
    //             sh 'python3 src/main.py --step commit'
    //         }
    //     }
    // }
    
    post {
        always {
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
            script {
                env.PASSWORD = ""
            }
        }
        // success {
        //     echo "PA Automation completed successfully!"
        //     echo "HA Configuration: ${params.HA1_INTERFACE} (Control), ${params.HA2_INTERFACE} (Data)"
        //     echo "Configuration committed and synced to both firewalls"
        // }
        // failure {
        //     echo "PA Automation failed. Check logs for details."
        // }
    }
}