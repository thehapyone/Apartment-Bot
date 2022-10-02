import json
from typing import Optional, Union, Tuple, NamedTuple
import hashlib
import logging
import os
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

# Configuring Selenium
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--ignore-certificate-errors')

# Logger
logger = logging.getLogger("scrapper_logger")
logger.setLevel(logging.INFO)

# get the google api key
api_key = os.environ.get('GOOGLE_API_KEY')
USERNAME = os.environ.get('SITE_USERNAME')
PASSWORD = os.environ.get('SITE_PASSWORD')
MAX_RENT = int(os.environ.get('MAX_RENT', "15000"))
MAX_DISTANCE = int(os.environ.get('MAX_DISTANCE', 18))


class Apartment(NamedTuple):
    """
    A named tuple class for an apartment entity
    """
    location: str
    link: str
    area: str
    rent: str
    rooms: str
    distance: Optional[str]
    time: Optional[str]
    unique_id: str


class Scrapper:
    """
    The scrapper entry class

    :param str url: The housing url
    :param str google_api_key: The Google API key for accessing the map features
    """

    def __init__(self, url, google_api_key):
        self.url = url
        self._google_api_key = google_api_key
        self.house = self.initialize_soup()
        self.reference_location = "vasastan"
        self.driver = None
        # tracks if there is a login session
        self._session = False

    def initialize_soup(self) -> Optional[BeautifulSoup]:
        """Here we will initialize the apartment site details"""
        logging.info("Initializing soup")
        try:
            # Selenium configuration
            driver = webdriver.Chrome(options=options)
            driver.get(self.url)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
        except Exception:
            logger.error("Could not initialize Scrapper site object",
                         exc_info=True)
            return None
        return soup

    @staticmethod
    def website_wait(driver, timeout: int = 10):
        WebDriverWait(driver=driver, timeout=timeout).until(
            lambda x: x.execute_script(
                "return document.readyState === 'complete'")
        )

    def quit_browser(self):
        """Quit browser"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def login_to_site(self):
        """Logins to the lottery site"""
        # create a driver instance session
        self.driver = webdriver.Chrome(options=options)

        # login to the site
        login_url = "https://minasidor.wahlinfastigheter.se/Account/Login"
        self.driver.get(login_url)

        # wait the ready state to be complete
        self.website_wait(self.driver)

        self.driver.find_element(By.ID, "nav-logine-tab").click()
        self.driver.find_element(By.ID, "UserId").send_keys(USERNAME)
        self.driver.find_element(By.ID, "Password").send_keys(PASSWORD)

        # wait the ready state to be complete
        self.website_wait(self.driver)

        # Submit button
        element = self.driver.find_element(By.ID, "LoginButton")
        element.submit()

        # wait the ready state to be complete
        self.website_wait(self.driver)

        try:
            error = self.driver.find_element(
                By.CLASS_NAME,
                "validation-summary-errors")

            if error.text.strip() == "Inloggningen misslyckades.":
                logger.error("Unable to login to the website")
                self.driver.quit()
                return False
            logger.error(f"Login not successful. "
                         f"Validation error {error.text.strip()}")
            return False
        except NoSuchElementException:
            pass

        logger.info("Login successful")
        return True

    def apply_to_apartment(self, apartment: Apartment):
        """Apply to the apartment"""

        try:
            # register interest
            register_btn = self.driver.find_element(By.ID,
                                                    "btnRegisterInterest")
            register_btn.submit()
            logger.info(f"Successfully registered to apartment "
                        f"at {apartment.location}")
        except NoSuchElementException:
            logger.warning(f"Already registered to the apartment "
                           f"at {apartment.location}")

    def get_apartments_section(self) -> Union[Tag, NavigableString]:
        """Returns the BeautifulSoup section of the area of the apartment"""
        return self.house.find('div', class_='d-flex flex-wrap')

    def get_apartments(self) -> tuple:
        """Gets the current active apartments from the housing site"""
        # Gets the number of apartments
        no_of_apartment = self.no_of_apartments()
        if no_of_apartment == 0:
            return tuple()

        # Get the apartments
        apartments = self.get_apartments_section(). \
            find_all('div', class_='pl-0 pr-2 col-12 col-sm-6 col-xl-3 pb-2')

        # Login to the apartment
        self._session = self.login_to_site()
        if not self._session:
            logger.error("Unable to proceed with apartments.")

        apartment_lists = [self.get_apartment_details(apartment) for
                           apartment in apartments]
        return tuple(apartment_lists)

    def no_of_apartments(self) -> int:
        """Returns the no of current active apartments"""
        # Gets the section of the apartments counts are
        apartment_counts = self.get_apartments_section(). \
            find_all('div', class_='pl-0 pr-2 col-12 col-sm-6 col-xl-3 pb-2')
        return len(apartment_counts)

    def get_apartment_details(self, apartment_item: BeautifulSoup) -> \
            Optional[Apartment]:
        """Gets all the scraped details for each apartment"""
        apartment_pre = apartment_item.findNext().findNext()
        link = apartment_pre.find('a')['href']
        link = f"https://minasidor.wahlinfastigheter.se{link}"

        # Extract details
        try:
            self.driver.get(link)
            apartment_soup = BeautifulSoup(self.driver.page_source,
                                           'html.parser')
        except Exception:
            logger.error("Could not retrieve the apartment details",
                         exc_info=True)
            return None
        # creates the apartment object
        information = apartment_soup. \
            find('div', class_='sitecontent').find(
            'div', class_='card card-style-cc w-100 h-100'). \
            find('div', class_='row')

        apartment_infos = information.findNext()
        results = {'Link': link}

        location = apartment_soup. \
            find('div', class_='col-12 page-title-cc').findChildren()

        results['Location'] = f"{location[0].text.strip()}, " \
                              f"{location[1].text.strip()}"

        rent_section = apartment_infos. \
            find('div', class_='col-12 d-flex').findChildren('div')

        if not len(rent_section):
            # means apartment is already registered
            logger.warning(f"Already registered to the apartment "
                           f"at {results['Location']}")
            return None

        results['Rent'] = rent_section[0].text.strip()

        results['Size'] = rent_section[2].text.strip()

        results["Rum"] = apartment_infos. \
            find('p', class_="object-preview-headline-size-cc col-12") \
            .text.strip()

        # Get the location estimate
        location, distance, travel_time = self.location_estimate(
            destination=results['Location'])

        # Build the apartment object
        apartment = Apartment(
            location=location.strip(),
            link=link.strip(),
            area=results.get("Size", "").strip(),
            rent=results.get("Rent", "").strip(),
            rooms=results.get("Rum", "").strip(),
            distance=distance.strip(), time=travel_time.strip(),
            unique_id=hashlib.md5(f'{link.strip()}{location.strip()}'.encode())
                .hexdigest()
        )

        # Apply to the Apartment
        # self.apply_to_apartment(apartment)
        kr_removed = apartment.rent.split("kr")[0].strip()
        striped_rent = int("".join(kr_removed.split(" ")))
        distance_stripped = float(apartment.distance.split("km")[0].strip())
        if striped_rent <= MAX_RENT and distance_stripped <= MAX_DISTANCE:
            self.apply_to_apartment(apartment)
        else:
            logger.info(
                f"Apartment criteria not matched. "
                f"Criteria: {MAX_RENT}KR rent and {MAX_DISTANCE} KM")

        return apartment

    def location_estimate(self, destination: str) -> Optional[
        Tuple[Optional[str], Optional[str], Optional[str]]]:
        """
        Using the Google API to estimate the
        location distance and time from some reference point
        """

        # url variable store url
        url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'

        # Get method of requests module
        params = dict(
            origins=self.reference_location,
            destinations=destination,
            key=self._google_api_key
        )
        # return response object
        try:
            response = requests.get(url, params=params,
                                    verify=True).json()  # type: dict
        except Exception:
            logger.warning(
                f"Error occurred while communicating with Google distance matrix service.",
                exc_info=True)
            return None
        data = response.get('rows')[0].get('elements')[0]  # type: dict
        # Gets the correct location name according to the Google API
        try:
            location = response.get('destination_addresses')[0]
        except Exception:
            location = destination
        # status = data.get('status')
        try:
            distance = data.get('distance').get('text')
            travel_time = data.get('duration').get('text')
        except (AttributeError, KeyError):
            logger.warning(
                f"Distance and Travel time couldn't not be fetched. Data packet is "
                f"{json.dumps(data)}", exc_info=True)
            distance, travel_time = "", ""

        return location, distance, travel_time


#
# def find_unique_apartments(apartments: Tuple[Apartment]) -> Tuple[Apartment]:
#     """Returns a set of unique apartments that are not currently saved in the db"""
#     unique_apartments = []
#     for apartment in apartments:
#         unique_id = apartment.unique_id
#         # dynamodb fetch for apartment
#         result = table.get_item(
#             Key={
#                 'unique_id': unique_id
#             }).get("Item", None)
#         if result is None:
#             unique_apartments.append(apartment)
#         else:
#             logger.debug(f"Apartment with unique id {unique_id} is already present in db")
#
#     return tuple(unique_apartments)
#
#
# def add_apartments_to_db(apartments: Tuple[Apartment]):
#     """Adds the processed apartments to db to avoid processing again"""
#     for apartment in apartments:
#         try:
#             table.put_item(
#                 Item={**apartment._asdict()})
#         except Exception:
#             logger.warning(f"An error has occurred in saving apartment "
#                            f"with unique id {apartment.unique_id} to db.", exc_info=True)
#
#
# def publish_apartments(apartments: Tuple[Apartment]):
#     """Publish the Apartments to SNS topic for subscribers to react"""
#     apartment_message_list = []
#     for apartment in apartments:
#         message_list = [f'{key.capitalize()}: {value}' for key, value in apartment._asdict().items()]
#         message = "\n".join(message_list)
#         apartment_message = f"{message}\n\n"
#         apartment_message_list.append(apartment_message)
#
#     header = f"{len(apartments)} New apartments has been found. See below and apply to each one. \n"
#     deliver_message = header + "\n".join(apartment_message_list)
#     sms_message = f"{len(apartments)} New apartments has been found. See email and apply."
#
#     message_body = dict(
#         default=sms_message,
#         email=deliver_message
#     )
#     try:
#         publish_response = topic.publish(
#             Message=json.dumps(message_body),
#             Subject="URGENT - New Apartment(s) found",
#             MessageStructure='json'
#         )
#         logger.debug(f'Message has been published. MessageId - {publish_response.get("MessageId")}')
#     except Exception:
#         logger.error("Could not publish message to SNS topic", exc_info=True)
#     else:
#         # Save the apartments to the db if no error.
#         add_apartments_to_db(apartments)
#

def lambda_handler(event, context):
    """The handler for lambda invocation"""
    website = "https://minasidor.wahlinfastigheter.se/ledigt/lagenhet"
    scrapper = Scrapper(website, api_key)
    try:
        apartments = scrapper.get_apartments()
    except Exception:
        logger.error("An error has occurred", exc_info=True)
        scrapper.quit_browser()
        return {
            'status_code': 401,
            'status': 'failed'
        }
    logger.info(f"Apartments: {apartments}")

    scrapper.quit_browser()
    return {
        'status_code': 201,
        'status': 'success'
    }


if __name__ == '__main__':
    lambda_handler([], None)
