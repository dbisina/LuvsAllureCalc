#!/bin/bash

# Install Python packages
pip install --user -r requirements.txt

# Create directories for Chrome and ChromeDriver
mkdir -p $HOME/chrome
mkdir -p $HOME/chromedriver

# Install Chrome (User-level workaround)
CHROME_URL="https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
wget -q -O $HOME/chrome/google-chrome.deb $CHROME_URL
dpkg -x $HOME/chrome/google-chrome.deb $HOME/chrome/

# Add Chrome to PATH
export PATH="$HOME/chrome/opt/google/chrome:$PATH"

# Get the installed Chrome version
CHROME_VERSION=$($HOME/chrome/opt/google/chrome/google-chrome --version | awk '{ print $3 }' | cut -d'.' -f1)

# Download matching ChromeDriver version
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O $HOME/chromedriver/chromedriver_linux64.zip
unzip -q $HOME/chromedriver/chromedriver_linux64.zip -d $HOME/chromedriver/

# Add ChromeDriver to PATH
chmod +x $HOME/chromedriver/chromedriver
export PATH="$HOME/chromedriver:$PATH"

# Test installation
google-chrome --version
chromedriver --version
