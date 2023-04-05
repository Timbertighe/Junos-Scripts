
"""
Connects to an SRX and pushes template config

Usage:
    Take a single SRX, or a list of SRXs (CSV) to connect to
    Take a JSON file (accessible over HTTP) of config to apply
    Options:
        -v, --verbose: Show the config that's being applied
        -c, --commit: Commit the changes (otherwise the changes will be rolled back)

Authentication:
    Supports username and password for login to NETCONF over SSH
    Junos supports RSA keys, but this script currently does not

Restrictions:
    Requires JunosPyEZ to be installed
    Requres a username/password to connect
    Asynchronous processing is not supported

To Do:
    - None

Author:
    Luke Robertson - September 2022
"""




"""
Functions

log_entry()
    Logs information to a file
    The destination file is opened when the main script initialises, and is passed to this function
    The function logs the time and a message

cleanup()
    This is run when the script needs to end (may be due to an error)
    The log file location is passed, so it can be closed gracefully
    If an SQL connection exists, it will be closed too

srx_connect()
    Connects to an SRX using pyEZ
    Checks for, and handles errors if they occur
    Returns the string 'error' if there's a problem
    Returns the connection object if successful
"""


# Log results and errors to a file
def log_entry (message, file):
    file.write ('\n' + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + message)




# Cleanup and exit when there's errors, or the script finishes
def cleanup(logfile):
    logfile.close()
    sys.exit()




# Connect to an SRX
def srx_connect (host, log, user, password):
    log_entry ("Connecting to " + host, log)

    print (termcolor.colored('\n\n\nConnecting to ' + host, "yellow"))

    for i in range (len(host) + 14):
        print (termcolor.colored('-', "yellow"), end = '')
    print ('\n')

    try:
        dev = Device(host, user=user, password=password).open()
    except jnpr.junos.exception.ConnectRefusedError as e:
        print (termcolor.colored('\nConnection Refused\n', "red"))
        print ('Check SSH settings, including acceptable ciphers\n')
        print ('Check that SSH over NETCONF is enabled\n')
        log_entry ('connection error: ' + repr(e) + '\n', log)
        return ('error')
    except jnpr.junos.exception.ConnectTimeoutError as e:
        print (termcolor.colored('\nConnection timed out\n', "red"))
        print ('Check that the hostname or IP address is correct\n')
        print ('Check that the firewall is responding to requests\n')
        log_entry ('connection error: ' + repr(e) + '\n', log)
        return ('error')
    except jnpr.junos.exception.ConnectAuthError as e:
        print (termcolor.colored('\nAuthentication Failed\n', "red"))
        print ('Check the username and password\n')
        log_entry ('connection error: ' + repr(e) + '\n', log)
        return ('error')
    except jnpr.junos.exception.ConnectError as e:
        print ('There was an error connecting to the SRX: ' + repr(e))
        log_entry ('connection error: ' + repr(e) + '\n', log)
        return ('error')
    return (dev)









"""
MAIN
"""

import argparse
import datetime
import sys
import csv
import termcolor
import os
import getpass
import requests



# Junos PyEZ
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
import jnpr.junos.exception



# Constants
LOCATION = 'http://10.10.10.10/share/'
WEB_FILTERING = 'web-filtering.json'



# Prepare argument parsing
# Get a single host or a list of hosts
# Optionally get more detailed status of the hosts
helpmsg = "Push templates to SRX firewalls"
parser = argparse.ArgumentParser (description = helpmsg)
group = parser.add_mutually_exclusive_group()       # Accept a host or a list, but not both
group.add_argument ("host", nargs='?', help = "The host name or IP of the SRX")
group.add_argument ("-f", "--file", help = "Pass a CSV file, containing a list of hosts")
parser.add_argument ("-v", "--verbose", action='store_true', help = "Show all configuration changes")
parser.add_argument ("-c", "--commit", action='store_true', help = "Commit changes to config")
parser.add_argument ("filename", nargs=1, help = "The config file that you want to apply (as a URL, eg, http://10.16.162.44/proxy/web-filtering.json)")
args = parser.parse_args()



# Prepare logging
year = datetime.datetime.now().year
month = datetime.datetime.now().strftime("%B")
filename = 'srx-template-' + str(year) + '-' + month + '.log'
log = open(filename, "a")
log_entry ("Begin logging", log)




# Setup device connection
# This will use either a list of devices (in a CSV file, one host per line) or a manually specified host
os.system('color')                      # Enable coloured text
host_list = []
if args.file:
    with open(args.file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            host_list.append(row[0])
elif args.host:
    host_list.append(args.host)
else:
    print ('Please specify a host, or a CSV list of hosts')
    parser.print_help()
    log_entry ('Host not specified, terminating', log)
    cleanup(log)





# Check if this is a json file
url = args.filename[0]
if url.split(".")[-1] != 'json':
    print (termcolor.colored("This needs to be a .json file", 'red'))
    log_entry ('Bad file name given (not .json)\n', log)
    cleanup(log)

# Check if the file exists
try:
    request_response = requests.head(url)
except Exception as error:
    err = str(error).split("]")[1].replace("'))", "")
    print (termcolor.colored("Webserver error: " + err, 'red'))
    log_entry ('Error connecting to webserver (' + url + '): ' + err + '\n', log)
    cleanup(log)
if request_response.status_code != 200:
    print (termcolor.colored("File does not exist", 'red'))
    log_entry ('Bad file name given (can\'t be reached)\n', log)
    cleanup(log)


    

# Get the username and password
username = input("Username:")
if username == '':
    print(termcolor.colored('You can\'t have a blank username', 'red'))
    log_entry ('Error: blank username\n', log)
    cleanup(log)
  

try:
    password = getpass.getpass()
except Exception as error:
    print(termcolor.colored('ERROR getting password', 'red'), error)
    log_entry ('ERROR getting password\n' + error, log)
    cleanup(log)




# Connect to the list of hosts
for host in host_list:
    dev = srx_connect (host, log, username, password)
    if dev == 'error':
        continue

    print ('Hostname: ' + termcolor.colored(dev.facts['hostname'], 'green'))
    log_entry ('connected to: ' + dev.facts['hostname'], log)


    # Edit the config
    with Config(dev) as cu:
        
        # Check if there's any uncommitted config waiting
        compare = cu.diff()
        if compare:
            print (termcolor.colored("Uncommitted config found, skipping " + dev.facts['hostname'], "red"))
            log_entry (dev.facts['hostname'] + ' already has uncommitted config (skipping...)', log)
            continue

        # Load the new config
        try:
            cu.load(url=url, format='text')
        except Exception as error:
            category = (str(error).split()[0].split("("))[0]
            match category:
                case 'ConfigLoadError':
                    print ("Error Loading Config\n")
                    if str(error).split()[2] == 'bad_element:':
                        print ("Config file contains a bad element: " + str(error).split()[3])
                        log_entry ('ERROR writing config\n' + str(error), log)
                        print ("Rolling back changes")
                        cu.rollback()
                        cleanup(log)
                case 'RpcTimeoutError':
                    print ("A timeout occurred while trying to update the config\n")
                case 'LockError':
                    print ("Configuration cannot be locked. There may be uncommitted changes waiting, or another user has an exclusive lock")
                case _:
                    print ("A generic error has occurred\n")
            print (error)
            log_entry ('ERROR writing config\n' + str(error), log)
            cleanup(log)
        compare = cu.diff()
        if compare == None:
            print (termcolor.colored("No changes to commit", "green"))
        else:
            print (termcolor.colored("Additional configuration added to candidate config\n", "yellow"))
            if args.verbose:
                print (compare)
            if args.commit:
                print ("Committing Config...")
                try:
                    cu.commit()
                except Exception as error:
                    category = str(error).split()[0].split("(")[0]
                    match category:
                        case 'CommitError':
                            print ("An error has occurred while trying to commit the config\n")
                            print (str(error).split("message: ")[1])
                            print ("Rolling back changes\n")
                            cu.rollback()
                        case 'RpcTimeoutError':
                            print ("We've experienced an RPC timeout while trying to commit the config\n")
                            print ("Config may have applied before the timeout\n")
                        case _:
                            print ("An unexpected error has occurred while trying to commit the config\n")
                            print (error)
                            print ("Rolling back changes\n")
                            cu.rollback()
                print ("Done")
                log_entry ("Committed config to " + dev.facts['hostname'], log)
            else:
                print (termcolor.colored("Config will not be committed. Use --commit to commit changes", "red"))
                try:
                    cu.commit_check()
                except Exception as error:
                    category = str(error).split()[0].split("(")[0]
                    match category:
                        case 'CommitError':
                            print ("There is an error with this config\n")
                            print (str(error).split("message: ")[1])
                        case 'RpcTimeoutError':
                            print ("We've experienced an RPC timeout while testing the config\n")
                        case _:
                            print ("There is an error with this config\n")
                            print (error)
                cu.rollback()







# Close the session and the log
log_entry ("Finishing script gracefully\n", log)
print ('\n\n')
try:
    dev.close()
except:
    print ('')
cleanup(log)


