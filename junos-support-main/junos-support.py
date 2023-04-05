"""
Connects to a Junos device and generate support files
Optionally uploads the files to an FTP server

Usage:
    At a minimum, specify a host to connect to
        junos-support.py 10.10.10.10
    Optionally, add an FTP server to upload the files to
        junos-support.py 10.10.10.10 172.16.1.1/ftp_folder

Authentication:
    Supports username and password for login to NETCONF over SSH
    Junos supports RSA keys, but this script currently does not

Restrictions:
    Requires JunosPyEZ to be installed
    Requires the termcolor module to be installed
    Requres a username/password to connect
    Requires NetConf to be enabled on the target device

To Do:
    - Change the timeout for the shell connection, or add a retry

Author:
    Luke Robertson - October 2022
"""




# Standard modules
import argparse
import datetime
import termcolor
import getpass
import os
import sys
import time
import signal

# Junos PyEZ
from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell
import jnpr.junos.exception



# Connect to a Junos device
def junos_connect (host, user, password):
    # Print a nice status message
    print (termcolor.colored('\n\n\nConnecting to ' + host, "yellow"))
    for i in range (len(host) + 14):
        print (termcolor.colored('-', "yellow"), end = '')
    print ('\n')

    # Connect to the device
    try:
        dev = Device(host, user=user, password=password).open()
    except jnpr.junos.exception.ConnectRefusedError as e:
        print (termcolor.colored('\nConnection Refused\n', "red"))
        print ('Check SSH settings, including acceptable ciphers\n')
        print ('Check that SSH over NETCONF is enabled\n')
        sys.exit()
    except jnpr.junos.exception.ConnectTimeoutError as e:
        print (termcolor.colored('\nConnection timed out\n', "red"))
        print ('Check that the hostname or IP address is correct\n')
        print ('Check that the firewall is responding to requests\n')
        sys.exit()
    except jnpr.junos.exception.ConnectAuthError as e:
        print (termcolor.colored('\nAuthentication Failed\n', "red"))
        print ('Check the username and password\n')
        sys.exit()
    except jnpr.junos.exception.ConnectError as e:
        print ('There was an error connecting to the SRX: ' + repr(e))
        sys.exit()

    # Return an object, describing the connection to the Junos device
    return (dev)



# Send shell commands to the device
# Take the command to run, as well as the shell object, which should already be defined
def send_shell(command, shell):
    try:
        output = shell.run(command)
    except Exception as e:
        print ('An error has occurred')
        print ('Sometimes a device will get busy and reject the attempt')
        #print (e)
        return ('Shell error')

    # Cleanup the output before returning
    out_text = output[1].replace (command, "")      # Extract the actual message on the CLI
    out_text = out_text.replace("\r\r\n", "")       # Remove the excessive number of blank lines

    return (out_text)



# Get username and password
def authenticate():
    # Username and password will be returned as a dictionary
    d = {}
    
    # Ask for the username, confirm it's not blank
    try:
        d['username'] = input("Username:")
    except:
        print (termcolor.colored('\nInvalid value in username', 'red'))
        sys.exit()
    if d['username'] == '':
        print(termcolor.colored('You can\'t have a blank username', 'red'))
        sys.exit()

    # Securely get the password
    try:
        d['password'] = getpass.getpass()
    except Exception as error:
        print(termcolor.colored('ERROR getting password', 'red'), error)
        sys.exit()
    if d['password'] == '':
        print(termcolor.colored('You can\'t have a blank password', 'red'))
        sys.exit()

    return d


# Ctrl-C handler function
def handler(signum, frame):
    print (termcolor.colored('\nScript terminated by user', 'red'))
    dev.close()
    sys.exit()



# Main function
def main():
    # Enable coloured text
    os.system('color')

    # Get date for filnames
    date = str(datetime.date.today())

    # Ctrl-C handler
    signal.signal(signal.SIGINT, handler)

    
    # Prepare to parse command-line arguments
    helpmsg = "Junos support tool. Generate support files for a Junos device"
    parser = argparse.ArgumentParser (description = helpmsg)
    parser.add_argument ("host", nargs=1, help = "The host name or IP of the Junos device")
    parser.add_argument ("filename", nargs='?', help = "destination ftp server (eg, 10.16.162.125/backups)")
    args = parser.parse_args()
    host = args.host[0]


    # Get credentials (FTP optional, only if FTP server has been provided)
    print (termcolor.colored('Please provide Junos device credentials', 'yellow'))
    junos_creds = authenticate()

    if args.filename:
        print (termcolor.colored('Please provide FTP server credentials', 'yellow'))
        ftp_creds = authenticate()
        ftp_server = 'ftp://' + ftp_creds['username'] + ':' + ftp_creds['password'] + '@' + args.filename + '/'


    # Connect to the Junos device
    dev = junos_connect (host, junos_creds['username'], junos_creds['password'])
    print ('Hostname: ' + termcolor.colored(dev.facts['hostname'], 'green'))


    # Connect to the device shell (for sending CLI commands)
    shell = StartShell(dev, timeout=60)
    try:
        shell.open()
    except jnpr.junos.exception.ConnectError as e:
        print ('There was an error connecting to the Junos device: ' + repr(e))
        dev.close()
        sys.exit()


    # Request the device to generate the support file
    print (termcolor.colored('Generating a support file (/var/log/RSI-Support-' + dev.facts['hostname'] + '-' + date + '.txt)', 'green'))
    print (termcolor.colored('Please be patient, this can take a long time (up to 10 minutes in some cases)', 'yellow'))
    send_shell ('cli -c "request support information | save /var/log/RSI-Support-' + dev.facts['hostname'] + '-' + date + '.txt"', shell)


    # Close the shell and open a new one
    # This seems to make the next step more stable, for unknown reasons (blame Juniper I guess)
    shell.close
    shell = StartShell(dev, timeout=60)
    try:
        shell.open()
    except jnpr.junos.exception.ConnectError as e:
        print ('There was an error connecting to the Junos device: ' + repr(e))
        dev.close()
        sys.exit()
    

    # Request the device to create an archive of the logs
    print (termcolor.colored('Generating a support archive (/var/tmp/Support-' + dev.facts['hostname'] + '-' + date + '.tgz)', 'green'))
    send_shell ('cli -c "file archive compress source /var/log/* destination /var/tmp/Support-' + dev.facts['hostname'] + '-' + date + '.tgz"', shell)
   

    # Optionally, upload the archive to an FTP server
    if args.filename:
        print (termcolor.colored('Uploading to FTP (ftp://' + ftp_creds['username'] + ':*****@' + args.filename + '/)', 'green'))
        result = send_shell ('cli -c "file copy /var/tmp/Support-* ' + ftp_server + '"', shell)
        if 'could not fetch local copy of file' in result:
            print (termcolor.colored('Error, can\'t find the archive file to upload to FTP', 'red'))
        if 'Not logged in' in result:
            print (termcolor.colored('Error, can\'t upload to FTP, check your credentials', 'red'))


    # Gracefully close the shell
    shell.close()
    dev.close()



# Entry point
if __name__ == "__main__":
    main()
    
