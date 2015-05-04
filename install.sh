sudo apt-get update

sudo apt-get install firefox htop git python-dev python-pip libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb

sudo pip install -U pyvirtualdisplay beautifulsoup4 netlib pyasn1 PyOPenSSL mitmproxy python-dateutil tld pyamf psutil

# Install selenium v2.44.0
sudo pip install selenium==2.44.0

# Install firefox v35
wget https://ftp.mozilla.org/pub/mozilla.org/firefox/releases/35.0.1/linux-x86_64/en-US/firefox-35.0.1.tar.bz2
tar jxf firefox*.tar.bz2 -C ./
rm firefox*.tar.bz2
