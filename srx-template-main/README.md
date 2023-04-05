# srx-template
Push template config to SRX firewalls


### Script Usage:
    Take a single SRX, or a list of SRXs (CSV) to connect to
    Take a JSON file (accessible over HTTP) of config to apply
    Options:
        -v, --verbose: Show the config that's being applied
        -c, --commit: Commit the changes (otherwise the changes will be rolled back)

### Config Files
    A .json file, containing junos config, needs to exist on a web server that the SRX can contact
    The script will tell the SRX to merge this config with the candidate config.
    Use -v or --verbose to see what config has been added
    Use -c or --commit to commit these changes (if this is not added, no changes will be made)
    Optionally, add 'replace:' tags in front of some stanza to overwrite the config with changes (default only adds new config)

### Authentication:
    Supports username and password for login to NETCONF over SSH
    Junos supports RSA keys, but this script currently does not

### Restrictions:
    Requires JunosPyEZ to be installed
    Requres a username/password to connect
    Asynchronous processing is not supported

### To Do:
    - None

### Author:
    Luke Robertson - September 2022




