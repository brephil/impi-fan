#!/bin/bash

# Define paths
PYTHON_SCRIPT="ipmi_fan.py"
CONFIG_FILE="ipmi-fan-config.yaml"
SERVICE_NAME="ipmi-fan.service"
SOURCE_DIR="."  # Update this path to where your scripts are located
DEST_BIN_DIR="/usr/bin"
DEST_SYSTEMD_DIR="/etc/systemd/system"
DEST_CONFIG_DIR="/etc/ipmi-fan-control"

# Create the destination configuration directory if it doesn't exist
if [ ! -d "$DEST_CONFIG_DIR" ]; then
    sudo mkdir -p "$DEST_CONFIG_DIR"
    echo "Created directory $DEST_CONFIG_DIR."
fi

# Move the config file to /etc/ipmi-fan-control
source_config_path="${SOURCE_DIR}/${CONFIG_FILE}"
destination_config_path="${DEST_CONFIG_DIR}/${CONFIG_FILE}"

if [ -f "$source_config_path" ]; then
    sudo cp "$source_config_path" "$destination_config_path"
    echo "Moved $CONFIG_FILE to $destination_config_path."
else
    echo "Error: File $source_config_path not found!"
    exit 1
fi

# Check if the service is already enabled and active
if systemctl is-enabled "$SERVICE_NAME" &> /dev/null; then
    echo "Service $SERVICE_NAME is currently enabled. Stopping and disabling it..."

    # Stop the service
    sudo systemctl stop "$SERVICE_NAME"
    echo "Stopped $SERVICE_NAME."

    # Disable the service
    sudo systemctl disable "$SERVICE_NAME"
    echo "Disabled $SERVICE_NAME."
fi

# Move the selected Python script to /usr/bin
source_path="${SOURCE_DIR}/${PYTHON_SCRIPT}"
destination_path="${DEST_BIN_DIR}/${PYTHON_SCRIPT}"

if [ -f "$source_path" ]; then
    sudo cp "$source_path" "$destination_path"
    echo "Moved $PYTHON_SCRIPT to $destination_path."
else
    echo "Error: File $source_path not found!"
    exit 1
fi

# Update the ipmi-fan.service file with the selected script name and config path
sed -i "s|ExecStart=/usr/bin/python3 /usr/bin/ipmi-fan.py|ExecStart=/usr/bin/python3 /usr/bin/${PYTHON_SCRIPT} --config ${DEST_CONFIG_DIR}/${CONFIG_FILE}|g" "${SOURCE_DIR}/${SERVICE_NAME}"

# Move ipmi-fan.service to /etc/systemd/system
source_service_path="${SOURCE_DIR}/${SERVICE_NAME}"
destination_service_path="${DEST_SYSTEMD_DIR}/${SERVICE_NAME}"

if [ -f "$source_service_path" ]; then
    sudo mv "$source_service_path" "$destination_service_path"
    echo "Moved $SERVICE_NAME to $destination_service_path."
    
    # Reload systemd daemon to recognize the new service file
    sudo systemctl daemon-reload
    echo "Reloaded systemd daemon."
else
    echo "Error: File $source_service_path not found!"
    exit 1
fi

# Enable and start the service
sudo systemctl enable "$SERVICE_NAME"
echo "Enabled $SERVICE_NAME."

sudo systemctl start "$SERVICE_NAME"
echo "Started $SERVICE_NAME."

# Add a delay before checking the status of the service
sleep 5  # Pause for 5 seconds

# Check the status of the service
status=$(systemctl is-active "$SERVICE_NAME")

if [ "$status" = "active" ]; then
    echo "Service $SERVICE_NAME is running successfully."
else
    echo "Failed to start service $SERVICE_NAME. Current status: $status"
    exit 1
fi

echo "Setup completed successfully."