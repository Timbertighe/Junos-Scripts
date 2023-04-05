"""
Connects to a Junos device and issues a reboot command

Usage:
    TBA

Authentication:
    Supports username and password for login to NETCONF over SSH
    Junos supports RSA keys, but this script currently does not

Restrictions:
    Requires JunosPyEZ to be installed
    Requres a username/password to connect
    Requires NETCONF to be enabled on the target device

To Do:
    TBA

Author:
    Luke Robertson - March 2023
"""

# 'SW' is the 'Software Utility' class
# This is used for upgrades, file copies, reboots, etc
from jnpr.junos import Device
from jnpr.junos.utils.sw import SW
from jnpr.junos.exception import ConnectError
from jnpr.junos.exception import RpcError
from datetime import datetime

# User details, needs to be secured
USER = 'user'
PASS = 'password'
HOST = 'host-or-ip'


# Reboot a device under various conditions
#   Now, in a particular time, at a particular time
# This is a function built into the junosPyEz library
#   We don't need to keep connection objects and send CLI commands
def reboot(device, user, password, **kwargs):
    '''
    Reboots a Junos device
    'time' parameter (datetime object) - Reboot at a time
    'duration' parameter (positive integer) - Reboot in a given time (minutes)
    No parameter - Reboot immediately
    '''
    
    print(f"Connecting to {device}...")
    
    # Connect to the device
    try:
        with Device(host=device, user=user, passwd=password) as dev:
            # Instantiate the 'Software Utility' class
            try:
                sw = SW(dev)
            except Exception as err:
                print("Could not create the software class")
                print(err)
                return

            # If there are no parameters, reboot now
            if kwargs == {}:
                print("Rebooting now")
                result = sw.reboot()

            # If the 'time' parameter is present, reboot then
            elif 'time' in kwargs:
                if kwargs['time'] < datetime.now():
                    print("This time is in the past")
                    return
                
                print(f"Rebooting at {kwargs['time']}")
                # Convert the time to a format junos uses
                junos_format = kwargs['time'].strftime("%y%m%d%H%M")
                result = sw.reboot(at=junos_format)

            # If the 'duration' parameter is present, reboot in that many minutes
            elif 'duration' in kwargs:
                if kwargs['duration'] < 1 or type(kwargs['duration']) != int:
                    print("This needs to be a positive whole integer in minutes")
                    return
                
                print(f"Rebooting in: {kwargs['duration']} minutes")
                result = sw.reboot(in_min=kwargs['duration'])

            # If there are parameters, but not 'time' or 'duration', there is an error
            else:
                print("You have used invalid parameters")
                print("  Pass no parameters to reboot now")
                print("  Pass 'time' parameter to reboot at a particular time")
                print("  Pass 'duration' parameter to reboot in a number of minutes")

            print(result)
    
    # Handle Connection error
    except ConnectError as err:
        print(f"There has been a connection error: {err}")

    # Handle an RPC error
    except RpcError as err:
        if 'another shutdown is running' in str(err):
            print("Unable to reboot, another reboot/shutdown has been scheduled")
        else:
            print(f"RPC Error has occurred: {err}")
    
    # Handle a generic error
    except Exception as err:
        print(f"Error was: {err}")





# Create a datetime object, representing the time to reboot
junos_time = datetime(year=2023, month=3, day=24, hour=3, minute=0)



# reboot(device='win-net-sw01', user=USER, password=PASS)
# reboot(device='win-net-sw01', user=USER, password=PASS, duration=40)
reboot(device='win-net-sw01', user=USER, password=PASS, time=junos_time)

