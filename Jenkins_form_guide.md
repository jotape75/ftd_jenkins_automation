# 📋 Jenkins Form Parameters Guide

Complete parameter reference for the Cisco FTD HA Automation Jenkins pipeline. Fill out the form in this exact order for optimal user experience.

## 📧 **1. Email Reporting**

**Email Report Destination:** `admin@company.com, netops@company.com`  
*Add email addresses to receive the report (comma-separated for multiple recipients)*

---

## 🔗 **2. FMC Connection Settings**

**FMC IP:** `192.168.0.201` - *FMC IP Address*

**FMC Username:** `api_user` - *FMC Username*

**FMC Password:** `[Hidden Field]` - *FMC Password*

---

## 🔥 **3. FTD Device Information**

**Cisco FTD 01 Hostname:** `ciscoftd01` - *Cisco FTD 01 Hostname*

**Cisco FTD 01 IP Address:** `192.168.0.202` - *Cisco FTD 01 IP Address*

**Cisco FTD 02 Hostname:** `ciscoftd02` - *Cisco FTD 02 Hostname*

**Cisco FTD 02 IP Address:** `192.168.0.203` - *Cisco FTD 02 IP Address*

**REGKEY:** `[Hidden Field]` - *Key for FMC Registration*

---

## 🔄 **4. High Availability Configuration**

**HA Interface:** `GigabitEthernet0/5` *(Dropdown)*  
*Options: GigabitEthernet0/3, GigabitEthernet0/4, GigabitEthernet0/5*

---

## 🌐 **5. INSIDE Interface Configuration**

**Inside Interface:** `GigabitEthernet0/1` *(Dropdown)*  
*Options: GigabitEthernet0/0, 0/1, 0/2, 0/3, 0/4*

**Inside Interface Name:** `Inside` - *Inside Interface Name*

**Inside Security Zone:** `Inside_Sec_Zone` - *Inside Security Zone*

**Inside Interface IP Address:** `192.168.1.1` - *Inside Interface IP Address*

**Inside Interface Subnet Mask:** `255.255.255.0` - *Inside Interface Subnet Mask*

**Inside Interface Standby IP:** `192.168.1.2` - *Inside Interface Standby IP*

**Inside Networks:** `192.168.1.0/24` - *Inside Networks*

---

## 🌍 **6. OUTSIDE Interface Configuration**

**Outside Interface:** `GigabitEthernet0/2` *(Dropdown)*  
*Options: GigabitEthernet0/0, 0/1, 0/2*

**Outside Interface Name:** `Outside` - *Outside Interface Name*

**Outside Security Zone:** `Outside_Sec_Zone` - *Outside Security Zone*

**Outside Interface IP Address:** `10.0.0.1` - *Outside Interface IP Address*

**Outside Interface Subnet Mask:** `255.255.255.0` - *Outside Interface Subnet Mask*

**Outside Interface Standby IP:** `10.0.0.2` - *Outside Interface Standby IP*

**Outside Networks:** `10.0.0.0/24` - *Outside Networks*

---

## 🏢 **7. DMZ Interface Configuration**

**DMZ Interface:** `GigabitEthernet0/3` *(Dropdown)*  
*Options: GigabitEthernet0/0, 0/1, 0/2*

**DMZ Interface Name:** `DMZ` - *DMZ Interface Name*

**DMZ Security Zone:** `DMZ_Sec_Zone` - *DMZ Security Zone*

**DMZ Interface IP Address:** `172.16.1.1` - *DMZ Interface IP Address*

**DMZ Interface Standby IP:** `172.16.1.2` - *DMZ Interface Standby IP*

**DMZ Interface Subnet Mask:** `255.255.255.0` - *DMZ Interface Subnet Mask*

**DMZ Networks:** `172.16.1.0/24` - *DMZ Networks*

---

## 🛡️ **8. Routing Configuration**

**Default Route Gateway:** `10.10.10.1` - *Default Route Gateway*

---

## ⚙️ **9. Platform Settings**

**Platform Settings Name:** `Global Platform Settings` - *Platform Settings Name in FMC*

---

## ✅ **Deployment Process**

After filling out all parameters:

1. **Review Settings** - Double-check all IP addresses and hostnames
2. **Click "Build"** - Jenkins will start the automation pipeline
3. **Monitor Progress** - Watch real-time execution in Jenkins console
4. **Receive Email Report** - Comprehensive HTML report sent upon completion

### **Pipeline Stages:**
1. 🔧 **Setup** - Repository clone and dependency installation
2. 📝 **Template Update** - JSON files updated with your parameters
3. 🔑 **API Authentication** - FMC API key generation
4. 📱 **Device Registration** - FTD devices added to FMC
5. 🔄 **HA Configuration** - High Availability pairing setup
6. 🌐 **Network Configuration** - Objects, zones, interfaces, routing, NAT
7. 🚀 **Deployment** - Configuration pushed to FTD devices
8. 📧 **Email Report** - Status summary sent to recipients

### **Total Deployment Time:** ~15 minutes

---

## 💡 **Example Configuration**

```yaml
# Email & FMC
EMAIL_REPORT_DESTINATION: admin@company.com, devops@company.com
FMC_IP: 192.168.0.201
FMC_USERNAME: api_user

# FTD Devices
FW_HOSTNAME_01: ciscoftd01 (192.168.0.202)
FW_HOSTNAME_02: ciscoftd02 (192.168.0.203)
HA_INTERFACE: GigabitEthernet0/5

# Network Topology with Security Zones
INSIDE:  GigabitEthernet0/1 → 192.168.1.1/24 (Standby: 192.168.1.2) [Inside_Sec_Zone]
OUTSIDE: GigabitEthernet0/2 → 10.0.0.1/24    (Standby: 10.0.0.2)    [Outside_Sec_Zone]
DMZ:     GigabitEthernet0/3 → 172.16.1.1/24  (Standby: 172.16.1.2)  [DMZ_Sec_Zone]

# Network Objects
INSIDE_NETWORK: 192.168.1.0/24
OUTSIDE_NETWORK: 10.0.0.0/24
DMZ_NETWORK: 172.16.1.0/24

# Routing & Platform
DEFAULT_ROUTE_GATEWAY: 10.10.10.1
PLATFORM_SETTINGS_NAME: Global Platform Settings
```
