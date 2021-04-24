
# This has been created and tested for Supermicro X10 motherboard


import sys,os,time

## CPU THRESHOLD TEMPS
high_cpu_temp = 70             # will go HIGH when we hit
med_high_cpu_temp = 65
med_cpu_temp = 60              # will go MEDIUM when we hit, or drop below again
med_low_cpu_temp =55
low_cpu_temp = 50               # will go LOW when we fall below again


#SAS 
high_sas_temp = 90
med_sas_temp = 85
low_sas_temp = 80

#Max Temp overides
hdd_max_allowed = 50
dimm_max_allowed = 85 #part HMA84GR7MFR4N-TF
vrm_max_allowed = 85
pch_max_allowed = 80

#Zone 0 duty cycles
z0_high = 100
z0_med_high = 50
z0_med = 30
z0_med_low = 10
z0_low = 5

#Zone 1 duty cycles
z1_high = 100
z1_med_high = 50
z1_med = 40
z1_med_low = 10
z1_low = 5

#Define Cooling zones based on your setup
zone0 = ['CPU','VRM','DIMM'] #FAN1-6 (Compute Resources)
zone1 = ['SAS','HDD','PCH']  #FANA and FANB (Storage and PCI)

def get_temps():
    stream = os.popen('ipmitool -c sdr type Temperature')
    return stream.readlines()

def get_fan_mode():
	stream = os.popen('ipmitool raw 0x30 0x45 0x00')
	output = stream.read().strip()
	return int(output)

def set_override_duty_cycle():
	set_zone_duty_cycle(0,z0_high)
	set_zone_duty_cycle(1,z1_high)

def set_zone_duty_cycle(zone,duty_cycle):
    os.popen('ipmitool raw 0x30 0x70 0x66 0x01 ' + str(zone) + ' ' + str(duty_cycle))

def get_temp(dev,temps):
	for temp in temps:
		if dev in temp[0]:
			temp = temp[1]
			return temp

def get_high_temp(dev,temps):
	dev_temp = 0
	for temp in temps:
		if dev in temp[0]:
			if dev_temp < int(temp[1]):
				dev_temp = int(temp[1])
	return dev_temp

def populate_zone_temps(zone_devices,temps):
	zone_temps = []
	for temp in temps:
		for device in zone_devices:
			if device in temp and 'ns' not in temp:
				output = list(temp.split(","))
				zone_temps.append(output)
	return zone_temps

def get_fan_mode_code(fanmode):
	if (fanmode is 'standard'):
		return 0
	elif(fanmode is 'full'):
		return 1
	elif(fanmode is 'optimal'):
		return 2
	elif(fanmode is 'heavyio'):
		return 3
	else:
		return 99 #illegal fan mode

def set_fan_mode(fanmode):
	mode = get_fan_mode_code(fanmode)
	if (mode < 99):
		os.popen('ipmitool raw 0x30 0x45 0x01 ' + str(mode))
		time.sleep(5) 



# need to go to Full mode so we have unfettered control of Fans
current_fan_mode = get_fan_mode()
if(current_fan_mode != 1):
	set_fan_mode("full")


#Main loop here
while True:

	#load temps
	temps = get_temps()

	zone0_temps = populate_zone_temps(zone0,temps)
	zone1_temps = populate_zone_temps(zone1,temps)

	#Check Zone 0 Temps
	cpu_high_temp= get_high_temp('CPU',zone0_temps)
	vrm_high_temp= get_high_temp('VRM',zone0_temps)
	dimm_high_temp = get_high_temp('DIMM',zone0_temps)

	#check Zone 1 Temps
	sas_high_temp= get_high_temp('SAS',zone1_temps)
	hdd_high_temp= get_high_temp('HDD',zone1_temps)
	pch_high_temp = get_high_temp('PCH',zone1_temps)

	#check override temps first
	#chassis uses both zones too cool the HDD and backplane so we need to monitor and overide
	if (hdd_high_temp >= hdd_max_allowed):
		set_override_duty_cycle()
	else:
		#check zone 0
		#escalate zone 0 duty cycle if needed
		if (cpu_high_temp > high_cpu_temp or vrm_high_temp >= vrm_max_allowed or dimm_high_temp >= dimm_max_allowed):
			set_zone_duty_cycle(0,z0_high)
		elif (cpu_high_temp > med_high_cpu_temp):
	   		set_zone_duty_cycle(0,z0_med_high)
		elif (cpu_high_temp > med_cpu_temp):
	   		set_zone_duty_cycle(0,z0_med)
		elif (cpu_high_temp > med_low_cpu_temp):
	   		set_zone_duty_cycle(0,z0_med_low)
		elif (cpu_high_temp <= low_cpu_temp):
			set_zone_duty_cycle(0,z0_low)

		#check zone 1
		#escalate zone 1 duty cycle if needed
		if (sas_high_temp > high_sas_temp or pch_high_temp >= pch_max_allowed) or (hdd_high_temp >= hdd_max_allowed):
	   		set_zone_duty_cycle(1,z1_high)
		elif (sas_high_temp > med_sas_temp):
	   		set_zone_duty_cycle(1,z1_med)
		elif( sas_high_temp <= low_sas_temp):
			set_zone_duty_cycle(1,z1_low)
		
	time.sleep(1)
