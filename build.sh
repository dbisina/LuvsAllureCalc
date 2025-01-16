#!/bin/bash

# Create directory for Chrome and ChromeDriver
mkdir -p $HOME/chrome
mkdir -p $HOME/chromedriver

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Download and set up ChromeDriver in user directory
wget https://chromedriver.storage.googleapis.com/$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip
unzip chromedriver_linux64.zip -d $HOME/chromedriver/
chmod +x $HOME/chromedriver/chromedriver