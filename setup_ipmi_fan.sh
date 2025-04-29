#!/bin/bash

# Define paths
PYTHON_SCRIPTS=("ipmi-fan-superserver.py" "ipmi-fan.py")
SERVICE_NAME="ipmi-fan.service"
SOURCE_DIR="."  # Update this path to where your scripts are located
DEST_BIN_DIR="/usr/bin"
DEST_SYSTEMD_DIR="/etc/systemd/system"

# Prompt the user to choose which Python script to enable
echo "Please select which Python script to enable:"
for i in "${!PYTHON_SCRIPTS[@]}"; do
    echo "$((i + 1)): ${PYTHON_SCRIPTS[i]}"
done

read -p "Enter your choice (1 or 2): " choice

# Validate the user's input
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#PYTHON_SCRIPTS[@]}" ]; then
    echo "Invalid choice. Please select a valid option."
    exit 1
fi

# Assign the selected script to a variable
selected_script="${PYTHON_SCRIPTS[$((choice - 1))]}"

# Move the selected Python script to /usr/bin
source_path="${SOURCE_DIR}/${selected_script}"
destination_path="${DEST_BIN_DIR}/${selected_script}"

if [ -f "$source_path" ]; then
    sudo cp "$source_path" "$destination_path"
    echo "Moved $selected_script to $destination_path."
else
    echo "Error: File $source_path not found!"
    exit 1
fi

# Update the ipmi-fan.service file with the selected script name
sed -i "s|ExecStart=/usr/bin/python3 /usr/bin/ipmi-fan.py|ExecStart=/usr/bin/python3 /usr/bin/${selected_script}|g" "${SOURCE_DIR}/${SERVICE_NAME}"

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

# Check the status of the service
status=$(systemctl is-active "$SERVICE_NAME")

if [ "$status" = "active" ]; then
    echo "Service $SERVICE_NAME is running successfully."
else
    echo "Failed to start service $SERVICE_NAME. Current status: $status"
    exit 1
fi

echo "Setup completed successfully."