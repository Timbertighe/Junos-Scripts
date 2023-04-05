"""
Connects to a Junos device and restarts a process

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
from jnpr.junos.exception import ConnectError
from jnpr.junos.exception import RpcError
from lxml import etree

# User details, needs to be secured
USER = 'username'
PASS = 'password'
HOST = 'host-or-ip'


def restart(device, user, password, process, **kwargs):
    print(f"Connecting to {device}...")
    if process == 'forwarding':
        print("This will restart the forwarding process")
        print("You will lose access to the device temporarily")
        print("(5+ minutes for small devices)")

    # Connect to the device
    try:
        with Device(host=device, user=user, passwd=password) as dev:
            # Restart the process immediately (SIGKILL)
            if 'immediately' in kwargs and kwargs['immediately'] is True:
                result = dev.rpc.restart_daemon(
                    immediately=True,
                    daemon_name=process,
                )
                print("Restart Initiated (SIGKILL)")

                # When using 'immediately', only a True or False is returned
                if result:
                    print("Restart Complete")
                else:
                    print("There were problems restarting this service")
                    print("Maybe check the system logs")

            # No args means restart gracefully (SIGTERM)
            # If args are invalid, just a regular restart will do
            else:
                result = dev.rpc.restart_daemon(
                    daemon_name=process
                )
                print("Restart Initiated (SIGTERM)")
                print(etree.tostring(result, encoding='unicode'))

    # Handle Connection error
    except ConnectError as err:
        print(f"There has been a connection error: {err}")

    # Handle an RPC error
    except RpcError as err:
        # Special handling for the forwarding process, as it will disconnect us
        if process == 'forwarding':
            print(f"I have been disconnected from {device}")
            print("This is normal when restarting the forwarding process")

        # Handle errors where a process is not running
        elif 'subsystem not running' in str(err):
            print(f"The {process} process cannot be started")
            print("It is not in use on this system")

        # Handle a bad process name
        elif 'invalid daemon' in str(err):
            print(f"The {process} does not exist on this system")
            print("Maybe it's typed incorrectly?")

        # Handle other RPC errors
        else:
            print(f"RPC Error has occurred: {err}")

    # Handle a generic error
    except Exception as err:
        print(f"Error was: {err}")


restart(
    device=HOST,
    user=USER,
    password=PASS,
    process='firewall',
    immediately=True
)
