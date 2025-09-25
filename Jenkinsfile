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
    
    parameters {
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
        choice(name: 'INSIDE_CONFIG', 
               choices: ['GigabitEthernet0/0 | INSIDE | INSIDE_SEC_ZONE',
                         'GigabitEthernet0/1 | INSIDE | INSIDE_SEC_ZONE',
                         'GigabitEthernet0/2 | INSIDE | INSIDE_SEC_ZONE'], 
               description: 'Inside: Interface | Name | Security Zone')
        
        string(name: 'INSIDE_IP', defaultValue: '192.168.1.1', description: 'Inside Interface IP Address')
        string(name: 'INSIDE_MASK', defaultValue: '255.255.255.0', description: 'Inside Interface Subnet Mask')
        
        choice(name: 'OUTSIDE_CONFIG',
               choices: ['GigabitEthernet0/0 | OUTSIDE | OUTSIDE_SEC_ZONE',
                         'GigabitEthernet0/1 | OUTSIDE | OUTSIDE_SEC_ZONE', 
                         'GigabitEthernet0/2 | OUTSIDE | OUTSIDE_SEC_ZONE'],
               description: 'Outside: Interface | Name | Security Zone')
        
        string(name: 'OUTSIDE_IP', defaultValue: '10.0.0.1', description: 'Outside Interface IP Address')
        string(name: 'OUTSIDE_MASK', defaultValue: '255.255.255.0', description: 'Outside Interface Subnet Mask')
        
        choice(name: 'DMZ_CONFIG',
               choices: ['GigabitEthernet0/0 | DMZ | DMZ_SEC_ZONE',
                         'GigabitEthernet0/1 | DMZ | DMZ_SEC_ZONE',
                         'GigabitEthernet0/2 | DMZ | DMZ_SEC_ZONE'],
               description: 'DMZ: Interface | Name | Security Zone')
        
        string(name: 'DMZ_IP', defaultValue: '172.16.1.1', description: 'DMZ Interface IP Address')
        string(name: 'DMZ_MASK', defaultValue: '255.255.255.0', description: 'DMZ Interface Subnet Mask')

        // Default route
        string(name: 'DEFAULT_ROUTE_GATEWAY', defaultValue: '10.10.10.1', description: 'Default Route Gateway')
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
                    env.FMC_IP = params.FMC_IP
                    env.FMC_USERNAME = params.FMC_USERNAME
                    env.FMC_PASSWORD = params.FMC_PASSWORD
                    env.FW_HOSTNAME_01 = params.FW_HOSTNAME_01
                    env.FW_HOSTNAME_02 = params.FW_HOSTNAME_02
                    env.IP_ADD_FW_01 = params.IP_ADD_FW_01
                    env.IP_ADD_FW_02 = params.IP_ADD_FW_02
                    env.REGKEY = params.REGKEY
                    env.SSH_ADMIN_USERNAME = params.SSH_ADMIN_USERNAME
                    env.SSH_ADMIN_PASSWORD = params.SSH_ADMIN_PASSWORD
                    env.HA_INTERFACE = params.HA_INTERFACE
                    
                    // Parse combined interface configurations
                    def insideConfig = params.INSIDE_CONFIG.split(' \\| ')
                    def outsideConfig = params.OUTSIDE_CONFIG.split(' \\| ')
                    def dmzConfig = params.DMZ_CONFIG.split(' \\| ')
                    
                    // Set parsed interface values
                    env.INSIDE_INTERFACE = insideConfig[0]
                    env.INSIDE_INTERFACE_NAME = insideConfig[1]
                    env.INSIDE_SEC_ZONE = insideConfig[2]
                    env.INSIDE_IP = params.INSIDE_IP
                    env.INSIDE_MASK = params.INSIDE_MASK
                    
                    env.OUTSIDE_INTERFACE = outsideConfig[0]
                    env.OUTSIDE_INTERFACE_NAME = outsideConfig[1]
                    env.OUTSIDE_SEC_ZONE = outsideConfig[2]
                    env.OUTSIDE_IP = params.OUTSIDE_IP
                    env.OUTSIDE_MASK = params.OUTSIDE_MASK
                    
                    env.DMZ_INTERFACE = dmzConfig[0]
                    env.DMZ_INTERFACE_NAME = dmzConfig[1]
                    env.DMZ_SEC_ZONE = dmzConfig[2]
                    env.DMZ_IP = params.DMZ_IP
                    env.DMZ_MASK = params.DMZ_MASK

                    // Default route
                    env.DEFAULT_ROUTE_GATEWAY = params.DEFAULT_ROUTE_GATEWAY

                    sh 'python3 src/update_templates.py'
                    
                    echo "Configuration Summary:"
                    echo "Target FMC: ${params.FMC_IP}"
                    echo "FTD Devices: ${params.FW_HOSTNAME_01}(${params.IP_ADD_FW_01}), ${params.FW_HOSTNAME_02}(${params.IP_ADD_FW_02})"
                    echo "HA Interface: ${params.HA_INTERFACE}"
                    echo "INSIDE: ${insideConfig[0]}(${insideConfig[1]}) - ${params.INSIDE_IP}/${params.INSIDE_MASK} [${insideConfig[2]}]"
                    echo "OUTSIDE: ${outsideConfig[0]}(${outsideConfig[1]}) - ${params.OUTSIDE_IP}/${params.OUTSIDE_MASK} [${outsideConfig[2]}]"
                    echo "DMZ: ${dmzConfig[0]}(${dmzConfig[1]}) - ${params.DMZ_IP}/${params.DMZ_MASK} [${dmzConfig[2]}]"
                }
            }
        }
        stage('Generate FMC API Key') {
            steps {
                sh 'python3 src/main.py --step api_keys'
            }
        }
        
        // stage('Add devices to FMC') {
        //     steps {
        //         sh 'python3 src/main.py --step add_dev_fmc'
        //     }
        // }
        
        // stage('Configure HA Settings') {
        //     steps {
        //         sh 'python3 src/main.py --step conf_ha'
        //     }
        // }
        stage('Configure FTD') {
            steps {
                sh 'python3 src/main.py --step ftd_conf'
            }
        }
    }
    
    // Additional stages for future expansion
    // stages {
    //     stage('Configure Interfaces') {
    //         steps {
    //             sh 'python3 src/main.py --step interface_config'
    //         }
    //     }
        
    //     stage('Configure Security Zones') {
    //         steps {
    //             sh 'python3 src/main.py --step zone_config'
    //         }
    //     }
        
    //     stage('Configure Routing') {
    //         steps {
    //             sh 'python3 src/main.py --step routing_config'
    //         }
    //     }
        
    //     stage('Configure Access Policies') {
    //         steps {
    //             sh 'python3 src/main.py --step policy_config'
    //         }
    //     }
        
    //     stage('Configure NAT Rules') {
    //         steps {
    //             sh 'python3 src/main.py --step nat_config'
    //         }
    //     }
        
    //     stage('Commit & Deploy Configuration') {
    //         steps {
    //             sh 'python3 src/main.py --step commit_deploy'
    //         }
    //     }
    // }
    
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