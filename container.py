# Code is meant to inside container environments
import os

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scrapper import Scrapper

# Display Port
display_port = os.environ.get('DISPLAY_PORT')

# Configuring the Display
display = Display(visible=False, extra_args=[f':{display_port}'],
                  size=(1920, 1200))
display.start()

# Chrome configuration
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-tools")
chrome_options.add_argument("--no-zygote")
chrome_options.add_argument("--single-process")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument('--ignore-ssl-errors=yes')
chrome_options.add_argument("window-size=1920x1200")
chrome_options.add_argument("--user-data-dir=/tmp/chrome-user-data")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.binary_location = '/opt/chrome/chrome'

# get the Google api key
api_key = os.environ.get('GOOGLE_API_KEY')

# Selenium configuration
driver = webdriver.Chrome(
    executable_path='/opt/chromedriver/chromedriver',
    options=chrome_options,
    service_log_path='/tmp/chromedriver.log')


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
