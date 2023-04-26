"""
Connects to a Junos device and generate support files
Uploads the files to an FTP server

Usage:
    TBA

Authentication:
    Supports username and password for login to NETCONF over SSH
    Junos supports RSA keys, but this script currently does not

Restrictions:
    Requires JunosPyEZ to be installed
    Requres a username/password to connect
    Requires NetConf to be enabled on the target device

To Do:
    Secure juniper and FTP credentials

Changes:
    Updated the shell to connect using 'with'
    Updated the 'cli -c' command
    Enabled passing a timer to send_shell()

Author:
    Luke Robertson - April 2023
"""


# Standard modules
import datetime
import termcolor

# Junos PyEZ
from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell
import jnpr.junos.exception


J_HOST = "10.0.0.1"
J_USER = "admin"
J_PASSWORD = "password"
FTP_HOST = "10.10.20.1/backups"
FTP_USER = "admin"
FTP_PASS = "password"


# Connect to a Junos device
def junos_connect(host, user, password):
    try:
        dev = Device(host, user=user, password=password).open()
    except Exception as err:
        return err
    return (dev)


# Send shell commands to the device
# Take the command to run, as well as the shell object
def send_shell(cmd, dev, **kwargs):
    # Check for additional args
    #   'timeout' is the time to spend waiting for a response
    #   'this' is the expected output to look for
    #   https://junos-pyez.readthedocs.io/en/2.6.4/jnpr.junos.utils.html#module-jnpr.junos.utils.start_shell
    if 'timeout' in kwargs:
        timeout = kwargs['timeout']
    else:
        timeout = 60

    # Print the command we're going to run
    print(termcolor.colored(cmd, "yellow"))

    # Convert the raw junos command to something the API can work with
    command = f'cli -c \'{cmd}\''

    # Send the command
    try:
        with StartShell(dev, timeout=timeout) as shell:
            output = shell.run(command)

    except jnpr.junos.exception.ConnectError as err:
        print(termcolor.colored(
            'There was an error connecting to the Junos shell: ' + repr(err),
            "red"
        ))
        return err

    except Exception as err:
        print('An error has occurred')
        print('Sometimes a device will get busy and reject the attempt')
        return err

    # Cleanup the output before returning
    # Extract the actual message, and remove excessive blank lines
    out_text = output[1].replace(command, "")
    out_text = out_text.replace("\r\r\n", "")

    # Return the response from the device
    shell.close()
    return (out_text)


# Handle errors when they occur
def error_handler(err, dev):
    if isinstance(err, str):
        if 'could not fetch local copy of file' in err:
            print(termcolor.colored(
                "Error, can't find the archive file to upload to FTP",
                'red'
            ))
        elif 'Not logged in' in err:
            print(termcolor.colored(
                "Error, can't upload to FTP, check your credentials",
                'red'
            ))
        else:
            print(termcolor.colored(
                f"An error has occurred: {err}",
                'red'
            ))
    elif isinstance(err, jnpr.junos.exception.ConnectRefusedError):
        print(termcolor.colored('Connection Refused', "red"))
        print('Check SSH settings, including acceptable ciphers')
    elif isinstance(err, jnpr.junos.exception.ConnectTimeoutError):
        print(termcolor.colored('Connection timed out', "red"))
        print('Check that the hostname or IP address is correct')
        print('Check that SSH over NETCONF is enabled')
        print('Is this a Junos device?')
    elif isinstance(err, jnpr.junos.exception.ConnectAuthError):
        print(termcolor.colored('Authentication Failed', "red"))
        print('Check the username and password\n')
    elif isinstance(err, jnpr.junos.exception.ConnectUnknownHostError):
        print('This host is unknown. Check your spelling')
    elif isinstance(err, jnpr.junos.exception.ConnectError):
        print(f'There was an error connecting to the device: {repr(err)}')
    else:
        print("There was an unknown error connecting")
        print(f"Error: {repr(err)}")

    dev.close()


# Main function
def main(host):
    # Get date for filnames
    date = str(datetime.date.today())

    # Build the FTP URL
    ftp_url = f'ftp://{FTP_USER}:{FTP_PASS}@{FTP_HOST}/'

    # Connect to the Junos device; Should return a connection object
    # If the returned object is not right, handle the error
    dev = junos_connect(host, J_USER, J_PASSWORD)
    if not isinstance(dev, jnpr.junos.device.Device):
        error_handler(dev)
        return False

    # Get the hostname, as it is configured on the device
    hostname = dev.facts['hostname']

    # Request the device to generate the support file
    #   The timeout is set high, as it can take a long time to collect RSI
    #    on some platforms
    rsi_filename = f'/var/log/RSI-Support-{hostname}-{date}.txt'
    print(termcolor.colored(f'RSI filename: {rsi_filename}', 'green'))
    result = send_shell(
        f'request support information | save {rsi_filename}',
        dev,
        timeout=1800
    )
    print(result)

    # Request the device to create an archive of the logs
    log_filename = f'/var/tmp/Support-{hostname}-{date}.tgz'
    print(termcolor.colored(f'Archive filename: {log_filename}', 'green'))
    result = send_shell(
        f'file archive compress source /var/log/* destination {log_filename}',
        dev
    )
    if not isinstance(result, str):
        error_handler(result)
        return False

    # Upload the archive to an FTP server
    print(termcolor.colored(f'Uploading to {ftp_url}', 'green'))
    result = send_shell(
        f'file copy /var/tmp/Support-* {ftp_url}/',
        dev
    )
    if 'not' in result.lower():
        error_handler(result)

    # Gracefully close the device
    dev.close()


# Entry point
if __name__ == "__main__":
    print(termcolor.colored("Starting...", "green"))
    main(J_HOST)
