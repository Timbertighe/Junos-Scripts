"""
Prints the recommended Junos versions for Juniper devices

Requires the jtac_scrape.py module

Modules:
    3rd Party: datetime
    Internal: jtac_scrape

Classes:

    None

Functions

    None

Exceptions:

    None

Misc Variables:

    TBA

Author:
    Luke Robertson - June 2023
"""

from datetime import datetime
import jtac_scrape as scraper


# Collect the recommended Junos versions for Juniper devices
if __name__ == "__main__":
    # URL of the web page
    url = "https://supportportal.juniper.net/s/article/Junos-Software-Versions-Suggested-Releases-to-Consider-and-Evaluate?language=en_US"

    # Create an instance of the scraper
    jtac = scraper.JtacScraper(url)

    # Get all recommended releases
    print("\nGetting EX series")
    info = jtac.get_ex()
    for item in info['ex']:
        print("Model:", item['model'])
        print("Recommended:", item['recommended'])
        if type(item['updated']) == datetime:
            print("Updated:", item['updated'].date(), '\n')

    print("\nGetting ACX series")
    info = jtac.get_acx()
    for item in info['acx']:
        print("Model:", item['model'])
        print("Recommended:", item['recommended'])
        if type(item['updated']) == datetime:
            print("Updated:", item['updated'].date(), '\n')

    print("\nGetting PTX series")
    info = jtac.get_ptx()
    for item in info['ptx']:
        print("Model:", item['model'])
        print("Recommended:", item['recommended'])
        if type(item['updated']) == datetime:
            print("Updated:", item['updated'].date(), '\n')

    print("\nGetting MX series")
    info = jtac.get_mx()
    for item in info['mx']:
        print("Model:", item['model'])
        print("Recommended:", item['recommended'])
        if type(item['updated']) == datetime:
            print("Updated:", item['updated'].date(), '\n')

    print("\nGetting NFX series")
    info = jtac.get_nfx()
    for item in info['nfx']:
        print("Model:", item['model'])
        print("Recommended:", item['recommended'])
        if type(item['updated']) == datetime:
            print("Updated:", item['updated'].date(), '\n')

    print("\nGetting QFX series")
    info = jtac.get_qfx()
    for item in info['qfx']:
        print("Model:", item['model'])
        print("Recommended:", item['recommended'])
        if type(item['updated']) == datetime:
            print("Updated:", item['updated'].date(), '\n')

    print("\nGetting SRX series")
    info = jtac.get_srx()
    for item in info['srx']:
        print("Model:", item['model'])
        print("Recommended:", item['recommended'])
        if type(item['updated']) == datetime:
            print("Updated:", item['updated'].date(), '\n')
