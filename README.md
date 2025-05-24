# IPMI Fan Control Script

## Overview
This script is designed to control the fan speed on servers using Intelligent Platform Management Interface (IPMI) tools. The script monitors temperature readings from various components and adjusts the fan duty cycle based on predefined thresholds. This ensures optimal cooling of the server, preventing overheating while minimizing noise.

### Key Features
- Temperature Monitoring: Fetches temperature data from IPMI sensors.
- Fan Mode Control: Adjusts fan speed based on current temperatures.
- Configuration via YAML File: Allows customization of thresholds and duty cycles.
- Test Mode: Simulates the script's operation using a test file for local development.
- Logging: Provides detailed logs to help with debugging and monitoring.

### Requirements
- Python 3.x
- ipmitool installed on the server.
- Access to the IPMI interface of the server. 

### Installation
1. Clone the GitHub repository and navigate to the project directory then run the installation script:
~~~ Bash
git clone https://github.com/yourusername/ipmi-fan-control.git
cd ipmi-fan-control
chmod +x setup_ipmi_fan.sh
sudo ./setup_ipmi_fan.sh
~~~
2. The script will enable and start the systemd service for IPMI fan control. It also checks if the service is running successfully.


### Configuration
Edit the `/etc/ipmi-fan-control/config.yaml` file to set up thresholds and duty cycles for different fan modes. The default configuration is suitable for most use cases, but you can customize it as needed.

### Usage
To run the script manually, execute:  
~~~ Bash
python3 ipmi_fan_control.py
~~~
For testing purposes, you can use the test mode by providing a test file:  
~~~ Bash
python3 ipmi_fan_control.py --test /path/to/test_file.yaml
~~~

### Systemd Service
The script includes a systemd service file located at `/etc/systemd/system/ipmi-fan-control.service`. This allows the script to run as a background service on system startup. To enable and start the service, use the following commands:
~~~ Bash
sudo systemctl enable ipmi-fan-control.service
sudo systemctl start ipmi-fan-control.service
~~~ 
To check the status of the service, use:
~~~ Bash
sudo systemctl status ipmi-fan-control.service
~~~ 
To stop and disable the service, use:
~~~ Bash
sudo systemctl stop ipmi-fan-control.service
sudo systemctl disable ipmi-fan-control.service
~~~
### Logging
Logs are stored in `/var/log/ipmi-fan-control.log`. You can view them using `tail -f` or any other log viewer.




      


