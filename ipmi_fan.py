import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import yaml
import argparse

def get_component_thresholds(component_name, zone='zone0'):
    if 'zones' in config and zone in config['zones']:
        components = config['zones'][zone].get('components', {})
        if component_name in components:
            return components[component_name]['thresholds']
    return None

def get_temps():
    """
    Fetch temperature readings from IPMI using ipmitool.
    Returns a list of lines containing temperature data.
    """
    if TEST_MODE:
        # Use this line to read from the test file for local testing
        with open('test.out', 'r') as file:
            return file.readlines()
    else:
        # Uncomment the following line to use the actual command
        stream = os.popen('ipmitool -c sdr type Temperature')
        return stream.readlines()

def get_fan_mode():
    """
    Get the current fan mode using IPMI raw commands.
    Returns an integer representing the fan mode.
    """
    stream = os.popen('ipmitool raw 0x30 0x45 0x00')
    output = stream.read().strip()
    logging.debug(f"Current fan mode: {output}")
    return int(output)

def set_override_duty_cycle():
    """
    Set the duty cycle for both zones to high.
    """
    set_zone_duty_cycle(0, z0_high)
    set_zone_duty_cycle(1, z1_high)

def set_zone_duty_cycle(zone, duty_cycle):
    """
    Set the fan duty cycle for a specific zone using IPMI raw commands.
    
    :param zone: The zone number (0 or 1).
    :param duty_cycle: The desired duty cycle percentage.
    """
    if not TEST_MODE:
        os.popen('ipmitool raw 0x30 0x70 0x66 0x01 ' + str(zone) + ' ' + str(duty_cycle))
    logging.debug(f"Set zone {zone} duty cycle to {duty_cycle}")

def get_temp(dev, temps):
    """
    Get the temperature of a specific device from the list of temperatures.
    
    :param dev: The device name.
    :param temps: A list of tuples containing device names and their corresponding temperatures.
    :return: The temperature of the specified device.
    """
    for temp in temps:
        if dev in temp[0]:
            return int(temp[1])

def get_high_temp(devices, temps):
    """
    Get the highest temperature among a list of devices from the temperature data.
    
    :param devices: A list of device names to check.
    :param temps: A list of tuples containing device names and their corresponding temperatures.
    :return: The highest temperature found among the specified devices.
    """
    dev_temp = 0
    for temp in temps:
        if any(device in temp[0] for device in devices):
            dev_temp = max(dev_temp, int(temp[1]))
    return dev_temp

def populate_zone_temps(zone_devices, temps):
    """
    Populate a dictionary with the maximum temperatures of devices in a specific zone.
    
    :param zone_devices: A list of device names in the zone.
    :param temps: A list of tuples containing device names and their corresponding temperatures.
    :return: A dictionary mapping device names to their maximum temperatures.
    """
    device_temps = {}
    
    for temp_entry in temps:
        try:
            device, value, unit, status = temp_entry.strip().split(',')
            # Check if the status is 'ok'
            if status == 'ok':
                # Check if any zone_device is "in" the device name
                for zone_device in zone_devices:
                    if zone_device in device:
                        temp_value = int(value)
                        if zone_device not in device_temps or temp_value > device_temps[zone_device]:
                            device_temps[zone_device] = temp_value
        except Exception as e:
            logging.error(f"Error processing entry '{temp_entry}': {e}")
    
    return device_temps

def get_fan_mode_code(fanmode):
    """
    Convert a fan mode name to its corresponding code.
    
    :param fanmode: The fan mode name as a string.
    :return: The fan mode code as an integer, or 99 if the mode is unknown.
    """
    if fanmode == 'standard':
        return 0
    elif fanmode == 'full':
        return 1
    elif fanmode == 'optimal':
        return 2
    elif fanmode == 'heavyio':
        return 3
    else:
        return 99

def set_fan_mode(fanmode):
    """
    Set the fan mode using IPMI raw commands.
    
    :param fanmode: The desired fan mode as a string.
    """
    mode = get_fan_mode_code(fanmode)
    if mode < 99:
        os.popen('ipmitool raw 0x30 0x45 0x01 ' + str(mode))
        time.sleep(5) 
        logging.info(f"Set fan mode to {fanmode}")

# Determine the appropriate duty cycle based on individual device thresholds
def determine_duty_cycle(zone, component_temps, thresholds):
    high_thresholds = []
    med_high_thresholds = []
    med_thresholds = []
    med_low_thresholds = []

    # Use the correct variables in the if-else statements
    zone_str = 'zone0' if zone == 0 else 'zone1'

    for component, temp in component_temps.items():
        if temp is None:
            continue

        # Find the appropriate threshold for each component
        comp_thresholds = thresholds[zone_str].get(component, [])       
        high_thresholds.append(comp_thresholds['thresholds'][0] if len(comp_thresholds['thresholds']) > 0 else float('inf'))
        med_high_thresholds.append(comp_thresholds['thresholds'][1] if len(comp_thresholds['thresholds']) > 1 else float('inf'))
        med_thresholds.append(comp_thresholds['thresholds'][2] if len(comp_thresholds['thresholds']) > 2 else float('inf'))
        med_low_thresholds.append(comp_thresholds['thresholds'][3] if len(comp_thresholds['thresholds']) > 3 else float('inf'))

    max_temp = max(component_temps.values())
    max_component, _ = max(component_temps.items(), key=lambda item: item[1])

    # Use the correct variables in the if-else statements
    if any(temp > max(high_thresholds) for temp in component_temps.values()):
        set_zone_duty_cycle(zone, z0_high if zone == 0 else z1_high)
        logging.info(f"Zone {zone}: Max temp {max_temp} from component '{max_component}' is above it's high threshold. Setting duty cycle to HIGH.")
    elif any(temp > max(med_high_thresholds) for temp in component_temps.values()):
        set_zone_duty_cycle(zone, z0_med_high if zone == 0 else z1_med_high)
        logging.info(f"Zone {zone}: Max temp {max_temp} from component '{max_component}' is above it's medium-high threshold. Setting duty cycle to MEDIUM-HIGH.")
    elif any(temp > max(med_thresholds) for temp in component_temps.values()):
        set_zone_duty_cycle(zone, z0_med if zone == 0 else z1_med)
        logging.info(f"Zone {zone}: Max temp {max_temp} from component '{max_component}' is above it's medium threshold. Setting duty cycle to MEDIUM.")
    elif any(temp > max(med_low_thresholds) for temp in component_temps.values()):
        set_zone_duty_cycle(zone, z0_med_low if zone == 0 else z1_med_low)
        logging.info(f"Zone {zone}: Max temp {max_temp} from component '{max_component}' is above it's medium-low threshold. Setting duty cycle to MEDIUM-LOW.")
    else:
        set_zone_duty_cycle(zone, z0_low if zone == 0 else z1_low)
        logging.info(f"Zone {zone}: Max temp {max_temp} from component '{max_component}' is below it's low threshold. Setting duty cycle to LOW.")

# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="IPMI Fan Control Script")
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()
    return args.test

if __name__ == "__main__":

    # Set this flag to True to use test.out for local testing
    TEST_MODE = False  # Default value, can be overridden by command-line argument

    # Parse command-line arguments
    TEST_MODE = parse_arguments()

    # Set up logging with a rotating file handler if TEST_MODE is False
    if not TEST_MODE:
        log_handler = TimedRotatingFileHandler('/var/log/ipmi-fan.log', when='midnight', interval=1, backupCount=5)
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(log_formatter)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(log_handler)

        current_fan_mode = get_fan_mode()
        if current_fan_mode != 1:
            set_fan_mode("full")
    else:
        # Set up logging to console if TEST_MODE is True
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    # Load YAML configuration
    with open('ipmi-fan-config.yaml', 'r') as file:
        config = yaml.safe_load(file)


    z0_high = config['duty_cycles']['z0']['high']
    z0_med_high = config['duty_cycles']['z0']['med_high']
    z0_med = config['duty_cycles']['z0']['med']
    z0_med_low = config['duty_cycles']['z0']['med_low']
    z0_low = config['duty_cycles']['z0']['low']

    z1_high = config['duty_cycles']['z1']['high']
    z1_med_high = config['duty_cycles']['z1']['med_high']
    z1_med = config['duty_cycles']['z1']['med']
    z1_med_low = config['duty_cycles']['z1']['med_low']
    z1_low = config['duty_cycles']['z1']['low']

    zone0 = [component for component in config['zones']['zone0']['components']]
    zone1 = [component for component in config['zones']['zone1']['components']]

    # Extract thresholds for each zone and component
    thresholds = {}
    for zone, zone_config in config['zones'].items():
        components_thresholds = {}
        for component, temp_list in zone_config['components'].items():
            components_thresholds[component] = temp_list
        thresholds[zone] = components_thresholds




    while True:
        try:
            # Load temps
            temps = get_temps()

            zone0_temps = populate_zone_temps(zone0, temps)
            zone1_temps = populate_zone_temps(zone1, temps)

            logger.debug(f"Zone 0 temperatures: {zone0_temps}")
            logger.debug(f"Zone 1 temperatures: {zone1_temps}")

            determine_duty_cycle(0, zone0_temps, thresholds)
            determine_duty_cycle(1, zone1_temps, thresholds)

        except Exception as e:
            logging.error(f"An error occurred: {e}")

        time.sleep(1)