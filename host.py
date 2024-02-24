# Code is meant to run on windows or linux environment
# Great for debugging

import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scrapper import Scrapper

# Configuring Selenium
options = Options()
options.headless = False
options.add_argument("--window-size=1920,1200")
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--ignore-certificate-errors')

# get the Google api key
api_key = os.environ.get('GOOGLE_API_KEY')

# Selenium Driver configuration
driver = webdriver.Chrome(options=options)


def run():
    """The main entrypoint"""
    scrapper = Scrapper(api_key, driver)
    try:
        apartments = scrapper.get_apartments()
    except Exception:
        scrapper.logger.error("An error has occurred", exc_info=True)
    else:
        scrapper.logger.info(f"Scrapper Finished. Found apartments are:"
                             f" {apartments}")
    finally:
        scrapper.quit_browser()


if __name__ == '__main__':
    run()
