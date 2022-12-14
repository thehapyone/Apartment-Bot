# Apartment-Bot

House hunting in some cases is tiring and quite exhausting, but we still 
continue doing it because at the end of the day we still need a place to 
cater for our lives. 

## Getting Started
This project contains a set of codes that was used to be build a apartment 
bot capable of various apartment tasks. The bot is designed to work only 
with the [wahlin fastigheter housing agency](https://wahlinfastigheter.se/)

The apartment bot is built around the [Selenium framework](https://www.selenium.dev/) which is usually 
utilized for UI testing.

## Features
The bot is capable of the following:
 - Search for available apartments
 - Apply to new apartments
 - Apply to apartments based different criteria including
   - Apartment cost
   - Apartment distance from a reference point
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
The bot can be ran inside a virtual environment. Steps below
 - Download the Google chrome gecko driver - https://chromedriver.chromium.org/downloads
 - Activate a virtual environment: `Python -m venv venv`
 - Install the required packages - pip install -m requirements.txt
 - Configure the environmental variables.
   ```shell
   export GOOGLE_API_KEY="Your API Key"
   export SITE_USERNAME="The Username for the housing website"
   export SITE_PASSWORD="Password of the site"
   ```
 - Configure the optional variables
   ```shell
   export MAX_RENT="Max rent. Defaults is 15000KR"
   export MAX_DISTANCE="Max Distance"
   ```
 - Run the bot: 
   ```shell
   python main.py
   ```
### Run the bot as a container
A container image is also available to run the bot and it can run as just 
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
