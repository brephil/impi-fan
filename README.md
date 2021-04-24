# impi-fan

For anyone wishing to use stock fans on their Supermicro build this will help keep the noise down and make sure there is plenty of cooling available on tap.

I started with this project with the goal of keeping my SC-836 chasis unmodified keeping all orignal plug-in play fans in place.  This script works with any X10 generation Supermicro motherboard.

Note:
I found that active coolers SNK-P0048AP4 work best.  I have an air shoud as well but not sure it is really needed.  What I've noticed the shroud helped address CPU cooling with the passive coolers, but have not tested without the active coolers.

My temps under load (70-80%) are stable at 57c for each CPU (2 x E5-2660 V3).  43.7 dB is the average sound at full system load (duty cycle 30 is all that is needed).  Idle tems in the 30s.

As to the script:

I'm monitoring two zones:
zone0 = ['CPU','VRM','DIMM'] #FAN1-6 (Compute Resources)
zone1 = ['SAS','HDD','PCH']  #FANA and FANB (Storage and PCI)

zone0 = FAN0 - FAN6
zone1 = FANA and FANB

The script checks once a second and adjusts each zone unless a HDD exceeds a max temp and all fans go crazy full!

I have this running as a service using systemctl.  
