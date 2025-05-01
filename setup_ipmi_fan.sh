#!/bin/bash

# Define paths
PYTHON_SCRIPT="ipmi-fan.py"
SERVICE_NAME="ipmi-fan.service"
SOURCE_DIR="."  # Update this path to where your scripts are located
DEST_BIN_DIR="/usr/bin"
DEST_SYSTEMD_DIR="/etc/systemd/system"

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

# Update the ipmi-fan.service file with the selected script name
sed -i "s|ExecStart=/usr/bin/python3 /usr/bin/ipmi-fan.py|ExecStart=/usr/bin/python3 /usr/bin/${PYTHON_SCRIPT}|g" "${SOURCE_DIR}/${SERVICE_NAME}"

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