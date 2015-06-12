sudo apt-get update

sudo apt-get install firefox htop git python-dev python-pip libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb

sudo pip install -U pyvirtualdisplay beautifulsoup4 netlib pyasn1 PyOPenSSL python-dateutil tld pyamf psutil mitmproxy

# Install specific version of Firefox and selenium
# known to work well together.
sudo pip install selenium==2.46.0
wget https://ftp.mozilla.org/pub/mozilla.org/firefox/releases/37.0.2/linux-x86_64/en-US/firefox-37.0.2.tar.bz2
tar jxf firefox*.tar.bz2 -C ./
rm firefox*.tar.bz2
