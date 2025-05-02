import sys, os, time, logging
from logging.handlers import TimedRotatingFileHandler
import configparser
import yaml

# Set up logging with a rotating file handler
log_handler = TimedRotatingFileHandler('/var/log/ipmi-fan.log', when='midnight', interval=1, backupCount=5)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Load YAML configuration
with open('ipmi-fan-config.yaml', 'r') as file:
    config = yaml.safe_load(file)

high_component_temp = config['thresholds']['high_component_temp']
med_high_component_temp = config['thresholds']['med_high_component_temp']
med_component_temp = config['thresholds']['med_component_temp']
med_low_component_temp = config['thresholds']['med_low_component_temp']
low_component_temp = config['thresholds']['low_component_temp']

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


def get_temps():
    """
    Fetch temperature readings from IPMI using ipmitool.
    Returns a list of lines containing temperature data.
    """
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

current_fan_mode = get_fan_mode()
if current_fan_mode != 1:
    set_fan_mode("full")

def check_and_set_duty_cycle(zone, temps, high_threshold, med_high_threshold, med_threshold, med_low_threshold, low_threshold):
    """
    Check the maximum temperature in a zone and set the fan duty cycle accordingly.
    
    :param zone: The zone number (0 or 1).
    :param temps: A dictionary mapping device names to their temperatures.
    :param high_threshold: The high temperature threshold for setting the fan duty cycle.
    :param med_high_threshold: The medium-high temperature threshold.
    :param med_threshold: The medium temperature threshold.
    :param med_low_threshold: The medium-low temperature threshold.
    :param low_threshold: The low temperature threshold.
    """
    max_temp = 0
    for device in temps:
        if temps[device] > max_temp:
            max_temp = temps[device]
        logging.info(f"Device: {device}, Temperature: {temps[device]}")
    logging.info(f"Max temperature in Zone {zone}: {max_temp}")
    
    # Define thresholds for each zone based on YAML configuration
    if zone == 0:
        high_thresholds = [config['zones']['zone0']['components'][comp]['thresholds'][0] for comp in config['zones']['zone0']['components']]
        med_high_thresholds = [config['zones']['zone0']['components'][comp]['thresholds'][1] for comp in config['zones']['zone0']['components']]
        med_thresholds = [config['zones']['zone0']['components'][comp]['thresholds'][2] for comp in config['zones']['zone0']['components']]
        med_low_thresholds = [config['zones']['zone0']['components'][comp]['thresholds'][3] for comp in config['zones']['zone0']['components']]
        low_thresholds = [config['zones']['zone0']['components'][comp]['thresholds'][4] for comp in config['zones']['zone0']['components']]

    elif zone == 1:
        high_thresholds = [config['zones']['zone1']['components'][comp]['thresholds'][0] for comp in config['zones']['zone1']['components']]
        med_high_thresholds = [config['zones']['zone1']['components'][comp]['thresholds'][1] for comp in config['zones']['zone1']['components']]
        med_thresholds = [config['zones']['zone1']['components'][comp]['thresholds'][2] for comp in config['zones']['zone1']['components']]
        med_low_thresholds = [config['zones']['zone1']['components'][comp]['thresholds'][3] for comp in config['zones']['zone1']['components']]
        low_thresholds = [config['zones']['zone1']['components'][comp]['thresholds'][4] for comp in config['zones']['zone1']['components']]

    # Determine the appropriate duty cycle based on individual device thresholds
    if any(temp > high_threshold for temp in high_thresholds):
        set_zone_duty_cycle(zone, z0_high if zone == 0 else z1_high)
        logging.info(f"Zone {zone}: Max temp {max_temp} is above high threshold. Setting duty cycle to HIGH.")
    elif any(temp > med_high_threshold for temp in med_high_thresholds):
        set_zone_duty_cycle(zone, z0_med_high if zone == 0 else z1_med_high)
        logging.info(f"Zone {zone}: Max temp {max_temp} is above medium-high threshold. Setting duty cycle to MEDIUM-HIGH.")
    elif any(temp > med_threshold for temp in med_thresholds):
        set_zone_duty_cycle(zone, z0_med if zone == 0 else z1_med)
        logging.info(f"Zone {zone}: Max temp {max_temp} is above medium threshold. Setting duty cycle to MEDIUM.")
    elif any(temp > med_low_threshold for temp in med_low_thresholds):
        set_zone_duty_cycle(zone, z0_med_low if zone == 0 else z1_med_low)
        logging.info(f"Zone {zone}: Max temp {max_temp} is above medium-low threshold. Setting duty cycle to MEDIUM-LOW.")
    else:
        set_zone_duty_cycle(zone, z0_low if zone == 0 else z1_low)
        logging.info(f"Zone {zone}: Max temp {max_temp} is below low threshold. Setting duty cycle to LOW.")


while True:
    try:
        # Load temps
        temps = get_temps()
        
        zone0_temps = populate_zone_temps(zone0, temps)
        zone1_temps = populate_zone_temps(zone1, temps)

        logger.debug(f"Zone 0 temperatures: {zone0_temps}")
        logger.debug(f"Zone 1 temperatures: {zone1_temps}")
        
        check_and_set_duty_cycle(0, zone0_temps, high_component_temp, med_high_component_temp, med_component_temp, med_low_component_temp, low_component_temp)
        check_and_set_duty_cycle(1, zone1_temps, high_component_temp, med_high_component_temp, med_component_temp, med_low_component_temp, low_component_temp)
 
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    time.sleep(1)
