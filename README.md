# junos_scripts
Script templates to automate Junos tasks

## Prerequisites
    Install PyEZ
    https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/topics/task/junos-pyez-server-installing.html

## reboot.py
    Reboots devices in a given time, or at a given time

## JTAC.py
    Collects RSI, logs, and uploads them to an FTP server
    Useful for cases with JTAC

## restart-process.py
    Restarts a junos process
    Optionally pass 'immediately=True' to use SIGKILL
    
## packet_fragmentation.py
    Connect to an SRX, and get packet fragmentation counters
    A filtered version of 'show system statistics'
