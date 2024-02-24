import hashlib
import json
import logging
import os
import re
from typing import Optional, Union, Tuple, NamedTuple

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Logger
logger = logging.getLogger("scrapper_logger")
logger.setLevel(logging.INFO)

USERNAME = os.environ.get('SITE_USERNAME')
PASSWORD = os.environ.get('SITE_PASSWORD')
MAX_RENT = int(os.environ.get('MAX_RENT', "15000"))
MAX_DISTANCE = int(os.environ.get('MAX_DISTANCE', 18))
MINIMUM_SIZE = int(os.environ.get('MINIMUM_SIZE', 20))
MINIMUM_ROOM = int(os.environ.get('MINIMUM_ROOM', 1))
LONG_RENT_ONLY = bool(os.environ.get('LONG_RENT_ONLY', True))

# Define regular expressions for rent and size
rent_pattern = re.compile(r'(\d+ \d+ kr)')
size_pattern = re.compile(r'(\d+ m2)')


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
    is_short_rent: bool
    unique_id: str


def criteria_match(rent: int, distance: float,
                   size: int, rooms: int, is_short_rent: bool) -> bool:
    # Evaluates if the user criteria condition matched
    if rent <= MAX_RENT and \
            distance <= MAX_DISTANCE and \
            size >= MINIMUM_SIZE and \
            rooms >= MINIMUM_ROOM:
        if LONG_RENT_ONLY and is_short_rent:
            return False
        return True
    return False


def website_wait(driver, timeout: int = 10):
    WebDriverWait(driver=driver, timeout=timeout).until(
        lambda x: x.execute_script(
            "return document.readyState === 'complete'")
    )


class Scrapper:
    """
    The scrapper entry class

    :param str google_api_key: The Google API key for accessing the map features
    :param any driver: The web driver to use

    """

    def __init__(self, google_api_key, driver):
        self.url = "https://minasidor.wahlinfastigheter.se/ledigt/lagenhet"
        self._google_api_key = google_api_key
        self.driver = driver
        self.house = self.initialize_soup()
        self.reference_location = "vasastan"
        # tracks if there is a login session
        self._session = False
        self.logger = logger

    def initialize_soup(self) -> Optional[BeautifulSoup]:
        """Here we will initialize the apartment site details"""
        logging.info("Initializing soup")
        try:
            # Selenium configuration
            self.driver.get(self.url)
            # wait the ready state to be complete
            website_wait(self.driver)
            self.driver.find_element(By.ID, "btnApproveAll").click()
            # wait the ready state to be complete
            website_wait(self.driver)
        except Exception as error:
            print(error)
            logger.error("Could not initialize Scrapper site object",
                         exc_info=True)
            return None
        except NoSuchElementException:
            pass

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        return soup

    def quit_browser(self):
        """Quit browser"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def login_to_site(self):
        """Logins to the lottery site"""
        # login to the site
        login_url = "https://minasidor.wahlinfastigheter.se/Account/Login"
        self.driver.get(login_url)

        # wait the ready state to be complete
        website_wait(self.driver)

        self.driver.find_element(By.ID, "nav-logine-tab").click()
        self.driver.find_element(By.ID, "UserId").send_keys(USERNAME)
        self.driver.find_element(By.ID, "Password").send_keys(PASSWORD)

        # wait the ready state to be complete
        website_wait(self.driver)

        # Submit button
        element = self.driver.find_element(By.ID, "LoginButton")
        element.submit()

        # wait the ready state to be complete
        website_wait(self.driver)

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
            find_all('div', class_='pl-0 pr-2 col-12 col-sm-6 col-xl-4 pb-2')

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
        res = self.get_apartments_section()
        apartment_counts = self.get_apartments_section(). \
            find_all('div', class_='pl-0 pr-2 col-12 col-sm-6 col-xl-4 pb-2')
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

        is_short_rent = True if "korttidskontrakt" in str(
            information) else False

        apartment_infos = information.findNext()
        results = {'Link': link}

        location = apartment_soup. \
            find('div', class_='col-12 page-title-cc').findChildren()

        results['Location'] = f"{location[0].text.strip()}, " \
                              f"{location[1].text.strip()}"

        results["Rum"] = apartment_infos. \
            find('p', class_="object-preview-headline-size-cc col-12") \
            .text.strip()

        rent_section = apartment_infos.find('div', class_='col-12 d-flex').text

        if "Intresseanmäld" in rent_section:
            # means apartment is already registered
            logger.warning(f"Already registered to the apartment "
                           f"at {results['Location']}")
            return None

        # Search for matches in the rent section
        rent_match = rent_pattern.search(rent_section.strip())
        size_match = size_pattern.search(rent_section.strip())

        # Extract values if matches are found
        results['Rent'] = rent_match.group(1).strip() if rent_match else ""
        results['Size'] = size_match.group(1).strip() if size_match else ""

        # Get the location estimate
        location, distance, travel_time = self.location_estimate(
            destination=results['Location'])

        # Build the apartment object
        apartment = Apartment(
            location=location.strip(),
            link=link.strip(),
            is_short_rent=is_short_rent,
            area=results.get("Size", ""),
            rent=results.get("Rent", ""),
            rooms=results.get("Rum", "").split(" ")[0],
            distance=distance.strip(), time=travel_time.strip(),
            unique_id=hashlib.md5(f'{link.strip()}{location.strip()}'.encode())
            .hexdigest()
        )
        kr_removed = apartment.rent.split("kr")[0].strip()
        striped_rent = int("".join(kr_removed.split(" ")))
        distance_stripped = float(apartment.distance.split("km")[0].strip())
        area_striped = apartment.area.split("m2")[0].strip()

        try:
            check_criteria = criteria_match(striped_rent, distance_stripped,
                                            int(area_striped),
                                            int(apartment.rooms), is_short_rent)
        except Exception as error:
            logger.error(f"An error as occurred - {error}")
            check_criteria = False

        if check_criteria:
            self.apply_to_apartment(apartment)
        else:
            logger.info(
                f"Apartment criteria not matched. "
                f"Criteria: {MAX_RENT}KR rent and {MAX_DISTANCE} KM")
            logger.info(apartment)

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
