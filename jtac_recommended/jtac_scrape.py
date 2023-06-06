"""
Loads the JTAC recommended releases page through a given URL
URL is typically "https://supportportal.juniper.net/s/article/Junos-Software-Versions-Suggested-Releases-to-Consider-and-Evaluate?language=en_US"

Modules:
    3rd Party: time, BeautifulSoup, selenium, dateutil
    Internal: None

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

import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dateutil.parser import parse


class JtacScraper:
    """
    Read the JTAC recommended releases page
    Return a list of recommended releases

    Attributes
    ----------
    url : str
        URL of the JTAC page to scrape

    Methods
    -------
    __init__(url)
        Class constructor
    cleanup()
        Clean up strings for better formatting
    get_ex()
        Get the recommended releases for EX series
    get_acx()
        Get the recommended releases for ACX series
    get_ptx()
        Get the recommended releases for PTX series
    get_qfx()
        Get the recommended releases for QFX series
    get_mx()
        Get the recommended releases for MX series
    get_srx()
        Get the recommended releases for SRX series
    """

    def __init__(self, url):
        """
        Class constructor

        (1) Loads the web page, including JavaScript rendering
        (2) Loads the HTML content into Beautiful Soup
        (3) Finds the tables for each product line

        Parameters
        ----------
        url : str
            URL of the web page to scrape

        Raises
        ------
        None

        Returns
        -------
        None
        """

        # Setup values
        print("Setting up browser...")
        self.url = url

        # Setup the web browser options
        # This will run headless, without dumping too much to the terminal
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('log-level=3')

        # Open the web browser silently, and load the page
        print("Loading web page...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # This includes JavaScript, which is why we need the web browser
        #   Wait for the page to load and execute JavaScript before scraping
        #   Max of 10 x 2 sec attempts (4-8 seconds is usually enough)
        self.ex_series = None
        counter = 10
        while self.ex_series is None:
            print("Waiting for JavaScript to load...")
            time.sleep(2)
            html = driver.page_source

            # Parse the HTML content using Beautiful Soup
            soup = BeautifulSoup(html, 'html.parser')

            # Find the tables for each product line
            self.ex_series = soup.find(
                'table',
                summary="EX Series Ethernet Switches"
            )

            # Prevent an infinite loop
            counter -= 1
            if counter < 0:
                print("Unable to parse web page")
                print("stuck waiting for JavaScript")
                print("Closing browser...")
                driver.quit()
                return False

        # At this point we're safe to assume the rest of the tables are loaded
        self.acx_series = soup.find(
            'table',
            summary="ACX Series Service Routers"
        )

        self.mx_ptx_series = soup.find(
            'table',
            summary="J Series Service Routers"
        )

        self.nfx_series = soup.find(
            'table',
            summary="NFX Series Network Services Platform"
        )

        self.qfx_series = soup.find(
            'table',
            summary="QFX Series Service Routers"
        )

        self.srx_series = soup.find(
            'table',
            summary="SRX Series Services Gateways"
        )

        # Close the browser
        print("Closing browser...")
        driver.quit()
        print("Finished scraping")

    def cleanup(self, string):
        """
        The result from the website is a bit messy, so this will clean it up.

        Parameters
        ----------
        string : str
            String to clean up

        Raises
        ------
        None

        Returns
        -------
        cleaned : str
            Cleaned up model string
        """

        # Remove Non-breaking spaces
        cleaned = string.replace('\xa0', ' ')

        # Remove tabs
        while '\t' in cleaned:
            cleaned = cleaned.replace('\t', '/')

        # Remove duplicate spaces
        while '  ' in cleaned:
            cleaned = cleaned.replace('  ', ' ')

        # Handle spaces around forward slashes and duplicates
        cleaned = cleaned.replace(' / ', '/')
        cleaned = cleaned.replace(' /', '/')
        cleaned = cleaned.replace('/ ', '/')
        while '//' in cleaned:
            cleaned = cleaned.replace('//', '/')

        # Handle spaces around brackets
        cleaned = cleaned.replace(' )', ')')
        cleaned = cleaned.replace('( ', '(')

        # Remove trailing dots
        cleaned = cleaned.strip('.')

        # Remove Notes
        cleaned = cleaned.replace(" (See Note 1)", "")
        cleaned = cleaned.replace(" (See Note 2)", "")
        cleaned = cleaned.replace(" (See Note 3)", "")
        cleaned = cleaned.replace(" (See Note 4)", "")
        cleaned = cleaned.replace(' (see notes)', '')
        cleaned = cleaned.replace(' (*1)', '')
        cleaned = cleaned.replace(' (*2)', '')
        cleaned = cleaned.replace(' (*3)', '')

        # Special cases
        cleaned = cleaned.replace(' (Except the ones listed below)', '')
        cleaned = cleaned.replace(' (recommended)', '')
        cleaned = cleaned.replace(' (legacy)', '')
        cleaned = cleaned.replace(' (see note)', '')

        return cleaned

    def get_ex(self):
        """
        Get EX Series recommended releases

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        info : dict
            Dictionary containing model, recommended release, and last updated
        """

        # Setup a dictionary of information
        info = {
            "ex": []
        }

        # Find all table rows
        rows = self.ex_series.find_all('tr')

        # Extract and print the table data
        for row in rows:
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            # Skip empty rows
            if not row_data:
                continue

            # Get model info, and clean it up
            model = self.cleanup(row_data[0])

            model = model.split("/")
            for item in model:
                entry = {}
                entry['model'] = item

                # Get the recommended release
                release = self.cleanup(row_data[1])
                if 'latest' in release.lower():
                    latest = True
                else:
                    latest = False
                release = release.replace('Latest ', '')

                # Check if there are multiple releases
                if '/' in release:
                    release = release.split('/')
                if type(release) == list and latest is True:
                    new_release = []
                    for item in release:
                        new_release.append(item + ' (latest)')
                    entry['recommended'] = new_release
                else:
                    entry['recommended'] = release

                # Get the last updated date
                date = row_data[2].replace('\xa0', ' ')
                date = parse(date)
                entry['updated'] = date
                info['ex'].append(entry)

        return info

    def get_acx(self):
        """
        Get ACX Series recommended releases

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        info : dict
            Dictionary containing model, recommended release, and last updated
        """

        # Setup a dictionary of information
        info = {
            "acx": []
        }

        # Find all table rows
        rows = self.acx_series.find_all('tr')

        # Extract and print the table data
        for row in rows:
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            # Skip empty rows
            if not row_data:
                continue

            # Get the model
            model = self.cleanup(row_data[0])

            model = model.split("/")
            for item in model:
                entry = {}
                entry['model'] = item

                # Get the release info, strip out multiple spaces
                release = self.cleanup(row_data[1])
                if 'latest' in release.lower():
                    latest = True
                else:
                    latest = False
                release = release.replace('Latest ', '')

                # Check if there are multiple releases
                if '/' in release:
                    release = release.split('/')
                if type(release) == list and latest is True:
                    new_release = []
                    for item in release:
                        new_release.append(item + ' (latest)')
                    entry['recommended'] = new_release
                else:
                    entry['recommended'] = release

                # Get the date info
                date = row_data[2].replace('\xa0', ' ')
                date = parse(date)
                entry['updated'] = date

                # Add the entry to the dictionary
                info['acx'].append(entry)

        return info

    def get_ptx(self):
        """
        Get PTX Series recommended releases

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        info : dict
            Dictionary containing model, recommended release, and last updated
        """

        # Setup a dictionary of information
        info = {
            "ptx": []
        }

        # Find all table rows
        rows = self.mx_ptx_series.find_all('tr')

        # Extract and print the table data
        for row in rows:
            entry = {}
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            # Skip empty rows
            if not row_data:
                continue

            # Skip MX Series entries
            if 'MX' in row_data[0]:
                continue

            # Get the model
            model = self.cleanup(row_data[0])

            if '/' in model and 'PTX10008' not in model:
                model = model.split("/")
            elif ', ' in model:
                model = model.split(", ")
            entry['model'] = model

            # Get the release info
            release = self.cleanup(row_data[1])
            if 'latest' in release.lower():
                latest = True
            else:
                latest = False

            # Check if there are multiple releases
            if '/' in release:
                release = release.split('/')
            if type(release) == list and latest is True:
                new_release = []
                for item in release:
                    new_release.append(item + ' (latest)')
                entry['recommended'] = new_release
            else:
                entry['recommended'] = release

            entry['recommended'] = release

            # Get the date info
            date = row_data[2].replace('\xa0', ' ')
            if date is not None and date != '':
                date = parse(date)
            else:
                date = ''
            entry['updated'] = date

            # Add the entry to the dictionary
            info['ptx'].append(entry)

        return info

    def get_mx(self):
        """
        Get MX Series recommended releases

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        info : dict
            Dictionary containing model, recommended release, and last updated
        """

        # Setup a dictionary of information
        info = {
            "mx": []
        }

        # Find all table rows
        rows = self.mx_ptx_series.find_all('tr')

        # Extract and print the table data
        for row in rows:
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            # Skip empty rows
            if not row_data:
                continue

            # Skip PTX Series entries
            if 'PTX' in row_data[0]:
                continue

            # Get the model
            model = self.cleanup(row_data[0])

            if '/' in model and 'MIC' not in model:
                model = model.split("/")
            elif ', ' in model:
                model = model.split(", ")

            if type(model) is not list:
                model = [model]

            for item in model:
                entry = {}
                entry['model'] = item

                # Get the release info
                release = self.cleanup(row_data[1])
                if 'See MX Series' in release:
                    continue
                if 'latest' in release.lower():
                    latest = True
                else:
                    latest = False
                release = release.replace('Latest ', '')

                # Check if there are multiple releases
                if '/' in release:
                    release = release.split('/')
                if type(release) == list and latest is True:
                    new_release = []
                    for item in release:
                        new_release.append(item + ' (latest)')
                    entry['recommended'] = new_release
                else:
                    entry['recommended'] = release

                # Get the date info
                date = row_data[2].replace('\xa0', ' ')
                if date is not None and date != '':
                    date = parse(date)
                else:
                    date = ''
                entry['updated'] = date

                # Add the entry to the dictionary
                info['mx'].append(entry)

        return info

    def get_nfx(self):
        """
        Get NFX Series recommended releases

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        info : dict
            Dictionary containing model, recommended release, and last updated
        """

        # Setup a dictionary of information
        info = {
            "nfx": []
        }

        # Find all table rows
        rows = self.nfx_series.find_all('tr')

        # Extract and print the table data
        for row in rows:
            entry = {}
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            # Skip empty rows
            if not row_data:
                continue

            # Get the model
            model = self.cleanup(row_data[0])

            if '/' in model:
                model = model.split("/")
            entry['model'] = model

            # Get the release info
            release = self.cleanup(row_data[1])
            if 'latest' in release.lower():
                latest = True
            else:
                latest = False
            release = release.replace('Latest ', '')

            # Check if there are multiple releases
            if '/' in release:
                release = release.split('/')
            if type(release) == list and latest is True:
                new_release = []
                for item in release:
                    new_release.append(item + ' (latest)')
                entry['recommended'] = new_release
            else:
                entry['recommended'] = release

            # Get the date info
            date = row_data[4].replace('\xa0', ' ')
            date = parse(date)
            entry['updated'] = date

            # Add the entry to the dictionary
            info['nfx'].append(entry)

        return info

    def get_qfx(self):
        """
        Get QFX Series recommended releases

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        info : dict
            Dictionary containing model, recommended release, and last updated
        """

        # Setup a dictionary of information
        info = {
            "qfx": []
        }

        # Find all table rows
        rows = self.qfx_series.find_all('tr')

        # Extract and print the table data
        for row in rows:
            entry = {}
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            # Skip empty rows
            if not row_data:
                continue

            # Get the model
            model = self.cleanup(row_data[0])

            if model == 'Asptra Release Considerations':
                continue

            if '/' in model:
                model = model.split("/")

            if type(model) is not list:
                model = [model]

            for item in model:
                entry = {}
                entry['model'] = item

                # Get the release info
                release = self.cleanup(row_data[1])
                if 'latest' in release.lower():
                    latest = True
                else:
                    latest = False
                release = release.replace('Latest ', '')

                # Check if there are multiple releases
                if '/' in release:
                    release = release.split('/')
                if type(release) == list and latest is True:
                    new_release = []
                    for item in release:
                        new_release.append(item + ' (latest)')
                    entry['recommended'] = new_release
                else:
                    entry['recommended'] = release

                # Get the date info
                date = row_data[2].replace('\xa0', ' ')
                while '  ' in date:
                    date = date.replace('  ', ' ')
                date = parse(date)
                entry['updated'] = date

                # Add the entry to the list
                info['qfx'].append(entry)

        return info

    def get_srx(self):
        """
        Get SRX Series recommended releases

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        info : dict
            Dictionary containing model, recommended release, and last updated
        """

        # Setup a dictionary of information
        info = {
            "srx": []
        }

        # Check if a table was found
        rows = self.srx_series.find_all('tr')

        # Extract and print the table data
        for row in rows:
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            # Skip empty rows
            if not row_data:
                continue

            # Get the model
            model = self.cleanup((row_data[0]))

            if 'Products for which' in model:
                continue

            # Check if a linecard is specified
            linecard = ''
            if 'with' in model:
                linecard = model.split('with')[1]

            # Check for multiple models per line
            if '/' in model:
                model = model.split("/")
                new_model = []
                for item in model:
                    if linecard == '':
                        new_model.append(item)
                    else:
                        if 'with' in item:
                            continue
                        new_model.append(item + ' with' + linecard)
                model = new_model

            if type(model) is not list:
                model = [model]

            for item in model:
                entry = {}
                entry['model'] = item

                # Get the release info
                release = self.cleanup(row_data[1])
                if 'latest' in release.lower():
                    latest = True
                else:
                    latest = False

                # Check if there are multiple releases
                if '/' in release:
                    release = release.split('/')
                if type(release) == list and latest is True:
                    new_release = []
                    for item in release:
                        new_release.append(item + ' (latest)')
                    entry['recommended'] = new_release
                else:
                    entry['recommended'] = release

                entry['recommended'] = release

                # Get the date info
                date = row_data[3].replace('\xa0', ' ')
                date = parse(date)
                entry['updated'] = date

                # Add the entry to the list
                info['srx'].append(entry)

        return info
