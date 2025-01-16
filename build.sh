#!/bin/bash

#!/bin/bash

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p $HOME/chrome $HOME/chromedriver

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/trusted.gpg.d/google.gpg
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google.list
apt-get update && apt-get install -y google-chrome-stable

# Get Chrome version
CHROME_VERSION=$(google-chrome --version | awk '{ print $3 }' | cut -d '.' -f 1)

# Download ChromeDriver
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O chromedriver.zip

# Extract and set up ChromeDriver
if [ -f "chromedriver.zip" ]; then
    unzip -q chromedriver.zip -d $HOME/chromedriver/
    chmod +x $HOME/chromedriver/chromedriver
    mv $HOME/chromedriver/chromedriver /usr/local/bin/
else
    echo "Failed to download ChromeDriver"
    exit 1
fi


export PATH="$HOME/chromedriver:$PATH"

# Test installation
google-chrome --version
chromedriver --version
