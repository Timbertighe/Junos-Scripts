# junos-support
Collect support information from Junos devices


### Script Usage:
    At a minimum, specify a host to connect to
        junos-support.py 10.45.20.1
    Optionally, add an FTP server to upload the files to
        junos-support.py 10.45.20.1 10.16.162.125/backups


### Authentication:
    Supports username and password for login to NETCONF over SSH
    Junos supports RSA keys, but this script currently does not
    When an FTP server is specified, the script will prompt for the username and password

### Restrictions:
    Requires JunosPyEZ and termcolor modules to be installed
    Requres a username/password to connect (to Junos and the FTP server)
    Requires NetConf to be enabled on the target device
    Asynchronous processing is not supported

### To Do:
    - None

### Author:
    Luke Robertson - October 2022




