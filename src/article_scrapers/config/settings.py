"""
Global settings for the French article scraping system.

This module contains configuration flags that control the behavior
of the entire scraping system.
"""

# Enable debug logging for detailed output
DEBUG = False

# Switch between live scraping and offline test mode
# True: Use local test files from test_data/ directory
# False: Scrape live websites
OFFLINE = False
