#!/usr/bin/bash

chrome_versions='999988'

# Download Chrome
echo "Downloading Chrome version $chrome_versions"
mkdir -p "/opt/chrome"
curl -Lo "/opt/chrome/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F${chrome_versions}%2Fchrome-linux.zip?alt=media"
unzip -q "/opt/chrome/chrome-linux.zip" -d "/opt/chrome/"
mv /opt/chrome/chrome-linux/* /opt/chrome/
rm -rf /opt/chrome/chrome-linux "/opt/chrome/chrome-linux.zip"

# Download Chromedriver
echo "Downloading Chromedriver version $chrome_versions"
mkdir -p "/opt/chromedriver"
curl -Lo "/opt/chromedriver/chromedriver_linux64.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F${chrome_versions}%2Fchromedriver_linux64.zip?alt=media"
unzip -q "/opt/chromedriver/chromedriver_linux64.zip" -d "/opt/chromedriver/"
mv "/opt/chromedriver/chromedriver_linux64/chromedriver" "/opt/chromedriver/chromedriver"
chmod +x "/opt/chromedriver/chromedriver"
rm -rf "/opt/chromedriver/chromedriver_linux64.zip" "/opt/chromedriver/chromedriver_linux64"
