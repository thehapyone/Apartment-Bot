# Apartment-Bot

House hunting in some cases is tiring and quite exhausting, but we still 
continue doing it because at the end of the day we still need a place to
cater for our lives.

## Getting Started

This project contains a set of codes that was used to be building an apartment
bot capable of various apartment tasks. The bot is designed to work only 
with the [wahlin fastigheter housing agency](https://wahlinfastigheter.se/)

The apartment bot is built around the [Selenium framework](https://www.selenium.dev/) which is usually 
utilized for UI testing.

## Features
The bot is capable of the following:
 - Search for available apartments
 - Apply to new apartments
 - Apply to apartments based on different criteria including
   - Apartment cost
   - Apartment distance from a reference point
   - Minimum number of rooms
   - Minimum apartment size
   - Only long term rents i.e not "korttidskontrakt"
 - Detect already applied apartments

## Location Estimation
The bot is capable of estimating the distance of an apartment from a 
reference location using the Google Map Matrix API.

## Usage
The apartment bot can be used in two ways:

### Requirements
 - Python >= 3.8
 - Google API Key

### Inside a virtual environment

The bot can be run inside a virtual environment. The steps below

- Download the Google Chrome gecko
  driver—https://chromedriver.chromium.org/downloads
 - Activate a virtual environment: `Python -m venv venv`
- Install the required packages — `pip install -m requirements.txt`
 - Configure the environmental variables.
   ```shell
   export GOOGLE_API_KEY="Your API Key"
   export SITE_USERNAME="The Username for the housing website"
   export SITE_PASSWORD="Password of the site"
   ```
 - Configure the optional variables
   ```shell
   # Set the max rent
   export MAX_RENT="15000"
   # Set the max distance to apply for. This distance is taking from the 
   # stockholm city center (vasatan) to the apartment. Usually the highly this 
   # value the farther the apartment is.
   export MAX_DISTANCE="15"
   # Set the minimum size to apply for.
   export MINIMUM_SIZE="40"
   # Set the minimum room count to apply for.
   export MINIMUM_ROOM="2"
    # Apply only to long term rents.
   export LONG_RENT_ONLY="True"
   ```
- Run the bot:
   ```shell
   python host.py
   ```
### Run the bot as a container

A container image is also available to run the bot, and it can run as just
every other docker container
 - Download the latest image for dockerhub - https://hub.docker.com/r/thehapyone/apartment-bot/tags
   ```shell
   docker pull thehapyone/apartment-bot:latest
   ```
 - Run the bot
   ```shell
   docker run --env GOOGLE_API_KEY="value1" --env SITE_USERNAME="value2" --env SITE_PASSWORD="value2" thehapyone/apartment-bot:latest
   ```
## Building
 You can add your own contribution and build the image with the attached 
 `Dockerfile`
 ```shell
   docker build -t apartment-bot:my_version .
 ```
## Licence
Feel free to use this code-base as the building blocks for your own bots and 
journey.
