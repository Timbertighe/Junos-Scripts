# JTAC Recommended Junos Versions
Defines a class that scrapes the JTAC recommended website to find the latest JTAC recommendations per model
Includes the date when the entry was last updated as a datetime object, which can be used for filtering

## Prerequisites
    Install Selenium
    Install Beautiful Soup

## jtac-scrape.py
    Includes the class, JtacScraper, that collects and parses the information we want

## jtac_versions.py
    An example of how we can use the class to collect version information and print it
