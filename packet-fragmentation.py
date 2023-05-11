"""
Connect to Junos devices and find packet fragmentation issues

Modules:
    External: jnpr.junos, traceback, lmxl.etree, xmltodict, json
    Internal: None

Classes:

    Netconf
        Connect to a Junos device using Netconf/SSH
        Run shell commands, RPC commands, and get the current configuration

Functions

    TBA

Exceptions:

    None

Misc Variables:

    TBA

Author:
    Luke Robertson - May 2023
"""

from jnpr.junos import Device as JunosDevice
from jnpr.junos.utils.start_shell import StartShell
import jnpr.junos.exception
from lxml import etree
import xmltodict
import traceback as tb
import json

HOST = '10.10.10.10'
USER = 'admin'
PASS = 'password'


class Netconf:
    """
    Connect to a Junos device using Netconf

    Supports being instantiated with the 'with' statement

    Attributes
    ----------
    TBA

    Methods
    -------
    error_handler
        Handle errors that are raised
    shell_commands
        Run commands in the Junos shell
    rpc_commands
        Run commands using the Junos RPC API
    get_config
        Get the current configuration
    """

    def __init__(self, host, user, password):
        """
        Class constructor

        Collects the details needed to connect to the Junos device
        Note: Only username/password is supported at this time (no SSH keys)

        Parameters
        ----------
        host : str
            The IP address or FQDN of the device to connect to
        user : str
            The username to connect with
        password : str
            The password to connect with

        Raises
        ------
        None

        Returns
        -------
        None
        """

        # Store the details needed to connect to the device
        self.host = host
        self.user = user
        self.password = password

        # An empty connection object
        # This will be populated when the 'connect' method is called
        self.dev = None

    def __enter__(self):
        """
        Called when the 'with' statement is used

        Calls the 'connect' method to connect to the device

        Parameters
        ----------
        None

        Raises
        ------
        jnpr.junos.exception.ConnectError
            If there is an error connecting to the device
        jnpr.junos.exception.ConnectTimeoutError
            If there is a timeout connecting to the device
        jnpr.junos.exception.ConnectRefusedError
            If the connection is refused
        jnpr.junos.exception.ConnectAuthError
            If the authentication fails
        jnpr.junos.exception.ConnectUnknownHostError
            If the host is unknown

        Returns
        -------
        self
            The instantiated object
        """

        try:
            self.dev = JunosDevice(
                self.host,
                user=self.user,
                password=self.password
            ).open()

        except jnpr.junos.exception.ConnectTimeoutError as err:
            print('Could not connect, there was a timeout')
            print(err)
            self.dev = None

        except jnpr.junos.exception.ConnectRefusedError as err:
            print("Error: Connection refused")
            print(err)
            self.dev = None

        except jnpr.junos.exception.ConnectAuthError as err:
            print("Error: Authentication failed")
            print(err)
            self.dev = None

        except jnpr.junos.exception.ConnectUnknownHostError as err:
            print("Error: Unknown host")
            print(err)
            self.dev = None

        except jnpr.junos.exception.ConnectError as err:
            print("Error: Connection error")
            print(err)
            self.dev = None

        except Exception as err:
            print('There was an unknown error connecting to the Junos device')
            print(err)
            self.dev = None

        finally:
            return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when the 'with' statement is finished

        Calls the 'disconnect' method to gracefully close the connection
            to the server

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        self
            None
        """

        # handle errors that were raised
        if exc_type:
            print(
                f"Exception of type {exc_type.__name__} occurred: {exc_value}"
            )

            self.error_handler(exc_value)
            print("error handler is done")

            if traceback:
                print("Traceback:")
                print(tb.format_tb(traceback))

            return False

        # If there were no errors and we have a connection, disconnect
        else:
            if self.dev:
                self.dev.close()

    def shell_commands(self, cmd, **kwargs):
        """
        Send shell commands to the device

        Parameters
        ----------
        cmd : str
            The command to run
        **kwargs
            Additional arguments to pass to the shell object
            'timeout' is the time to spend waiting for a response
                https://junos-pyez.readthedocs.io/en/2.6.4/jnpr.junos.utils.html#module-jnpr.junos.utils.start_shell

        Raises
        ------
        None

        Returns
        -------
        None
        """

        # If there is no connection to the device, return None
        if self.dev is None:
            return None

        # If a timeout was passed, use it, otherwise default to 60 seconds
        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
        else:
            timeout = 60

        # Convert the raw junos command to something the API can work with
        command = f'cli -c \'{cmd}\''

        # Connect to the device shell (for sending CLI commands)
        try:
            shell = StartShell(self.dev, timeout=timeout)
            shell.open()

        except jnpr.junos.exception.ConnectError as err:
            print('There was an error connecting to the Junos shell')
            print(err)
            return err

        # Attempt the command
        try:
            output = shell.run(command)

        except Exception as err:
            print('Connected to the shell, but the command could not be run')
            print('Sometimes a device will get busy and reject the attempt')
            return err

        # Cleanup the output before returning
        # Extract the actual message, and remove excessive blank lines
        out_text = str(output[1].replace(command, ""))
        out_text = out_text.replace("\r\r\n", "")

        # Remove trailing spaces and % signs
        if out_text.endswith(" "):
            out_text = out_text.rstrip()
        if out_text.endswith("%"):
            out_text = out_text.rstrip("%")

        # Return the response from the device
        shell.close()
        return (out_text)

    def error_handler(self, err):
        """
        Handle errors

        Parameters
        ----------
        err : Exception
            The error that was raised

        Raises
        ------
        None

        Returns
        -------
        None
        """

        if isinstance(err, str):
            error_string = repr(err)
            error_string = error_string.replace("% '", "")
            error_string = error_string.replace("cli -c \"\'", "")
            error_string = error_string.replace("\'cli -c", "")
            error_string = error_string.replace("\"", "<br>")
            error_string = error_string.replace("\\r\\n\\r\\n", "<br>")
            error_string = error_string.replace("\\r\\n", "<br>")

            print("Error: " + error_string)

        elif isinstance(err, jnpr.junos.exception.ConnectRefusedError):
            print("Error: Connection refused")

        elif isinstance(err, jnpr.junos.exception.ConnectAuthError):
            print("Error: Authentication failed")

        elif isinstance(err, jnpr.junos.exception.ConnectUnknownHostError):
            print("Error: Unknown host")

        elif isinstance(err, jnpr.junos.exception.ConnectError):
            print("Error: Connection error")

        else:
            print("Error: Unknown error")

    def rpc_commands(self, rpc_cmd, *args, **kwargs):
        """
        Send RPC commands to the device

        RPC commands can be found here:
        https://apps.juniper.net/xmlapi/operTags.jsp

        Or, in junos, pipe the command through 'display xml rpc' like this:
        'show interfaces terse | display xml rpc'
        https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/topics/task/junos-pyez-rpcs-executing.html

        Parameters
        ----------
        rpc_cmd : str
            The RPC command to run
            eg, 'get-interface-information'
        *args, **kwargs
            Additional arguments to pass to the RPC object
            eg, 'terse=True' or 'interface_name="ge-0/0/0"'

        Raises
        ------
        None

        Returns
        -------
        None
        """

        # If there is no connection to the device, return None
        if self.dev is None:
            return None

        # Send the command to the device
        try:
            rpc_call = getattr(self.dev.rpc, rpc_cmd)
            output = rpc_call(*args, **kwargs)
            output = etree.tostring(output, encoding='unicode')
            output = xmltodict.parse(output)

        except Exception as err:
            print('There was an error connecting to the Junos shell')
            print(err)
            output = err

        return output

    def get_config(self, **kwargs):
        """
        Get the configuration from a device
        If 'filter' is passed in kwargs, it will be used as the filter
            This is a list of strings, as multiple filters can be passed
            eg: '<configuration><system><services/></system></configuration>'

        Example filter, to get the interfaces:
        filter = ['interfaces']]

        Example filter, to get the system and protocols:
        filter = ['system', 'protocols']

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        None
        """

        # If there is no connection to the device, return None
        if self.dev is None:
            return None

        # Get the configuration from the device
        if 'filter' in kwargs:
            # Need to build an XML filter
            #   Start with the <configuration> tag
            filter = '<configuration>'

            # Work through each filter parameter
            for parameter in kwargs['filter']:
                # If the parameter has a '/' in it, it's a nested filter
                #   This is for things like 'system/services'
                if '/' in parameter:
                    # Split the parameter into a list
                    #   We need a reversed copy later
                    new_entry = parameter.split('/')
                    reversed = new_entry[::-1]

                    # Add each item to the filter string
                    for item in new_entry:
                        filter += f'<{item}>'

                    # The last item in the list is the actual filter
                    #   It needs to end with a '/>' instead of a '>'
                    filter = filter.rstrip('>')
                    filter += '/>'

                    # Close the rest of the tags
                    #   This is done by reversing the list, with a '</' added
                    for item in reversed[1:]:
                        filter += f'</{item}>'

                # Otherwise, it's a top-level filter
                #   Just add it to the filter string
                else:
                    filter += f'<{parameter}/>'

            #  Close the <configuration> tag
            filter += '</configuration>'

            try:
                config = self.dev.rpc.get_config(filter_xml=filter)

            except Exception as err:
                if 'bad_element' in str(err):
                    print('Error: The config filter is not valid')
                else:
                    print('Error getting config')
                    print(err)
                return None

        else:
            config = self.dev.rpc.get_config()

        # Convert the configuration to a dictionary
        config = etree.tostring(config, encoding='unicode')
        config = xmltodict.parse(config)

        return config


if __name__ == "__main__":
    with Netconf(host=HOST, user=USER, password=PASS) as dev:
        # Get packet fragmentation information
        stats = dev.rpc_commands('get-statistics-information')

    stats = stats['statistics']

    counters = {
        'tcp': {
            'received_duplicates': stats['tcp']['received-completely-duplicate-packet'],
            'received_out_of_order': stats['tcp']['received-out-of-order-packets'],
            'drops': stats['tcp']['drops'],
            'keepalive_timeout': stats['tcp']['keepalive-timeouts']
        },
        'ip': {
            'incorrect_version': stats['ip']['packets-with-incorrect-version-number'],
            'fragments_received': stats['ip']['fragments-received'],
            'frag_drop_nospace_dup': stats['ip']['fragments-dropped-due-to-outofspace-or-dup'],
            'frag_drop_queue_overflow': stats['ip']['fragments-dropped-due-to-queueoverflow'],
            'frag_drop_timeout': stats['ip']['fragments-dropped-after-timeout'],
            'output_fragments': stats['ip']['output-datagrams-fragmented'],
            'fragments_created': stats['ip']['fragments-created'],
            'cannot_fragment': stats['ip']['datagrams-that-can-not-be-fragmented']
        },
        'dpi': {
            'fragments_received': stats['tnp']['fragmented-packets-received'],
            'fragments_dropped': stats['tnp']['received-fragments-dropped'],
            'frag_reassembly_queue_flush': stats['tnp']['fragment-reassembly-queue-flushes']
        }
    }

    # Print the stats
    # print(json.dumps(stats, indent=4, sort_keys=True))
    print(json.dumps(counters, indent=4, sort_keys=True))
