#!/bin/bash

# Install Python packages
pip install -r requirements.txt

# Create directories
mkdir -p $HOME/chrome
mkdir -p $HOME/chromedriver

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Get the installed Chrome version
CHROME_VERSION=$(google-chrome --version | awk '{ print $3 }' | cut -d'.' -f1)

# Download matching ChromeDriver version
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip -d $HOME/chromedriver/

# Make ChromeDriver executable and move to expected location
chmod +x $HOME/chromedriver/chromedriver
mv $HOME/chromedriver/chromedriver /usr/local/bin/